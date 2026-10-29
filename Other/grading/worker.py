"""Trusted host-side runner. Student code executes only inside disposable containers."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import selectors
import time
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from manifest import load_assignments


COMPLETED = b'course-tests-completed\n'


def bounded_run(command, timeout, max_bytes=4096):
    """Drain a bounded completion channel; kill noisy or stalled processes."""
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as process:
        deadline = time.monotonic() + timeout
        output = bytearray()
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            try:
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise subprocess.TimeoutExpired(command, timeout)
                    if not selector.select(remaining):
                        raise subprocess.TimeoutExpired(command, timeout)
                    chunk = os.read(process.stdout.fileno(), 4096)
                    if not chunk:
                        return process.wait(timeout=max(0.01, deadline-time.monotonic())), bytes(output)
                    output.extend(chunk)
                    if len(output) > max_bytes:
                        process.kill()
                        return -1, b''
            finally:
                if process.poll() is None:
                    process.kill()


def execute(hw, source, trusted, image):
    results = []
    for task in hw['tasks']:
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            reference = trusted / hw['path']
            shutil.copytree(reference, work / 'hw', ignore=shutil.ignore_patterns('__pycache__', '.venv', '.pytest_cache'))
            # Only regular solution files may cross the trust boundary.
            for item in hw['tasks']:
                target = work / 'hw' / item['id'] / item['solution']
                candidate = source / hw['path'] / item['id'] / item['solution']
                if candidate.is_file() and not candidate.is_symlink() and candidate.resolve().is_relative_to(source.resolve()):
                    shutil.copyfile(candidate, target)
                else:
                    target.write_text('raise NotImplementedError("No solution submitted")\n')
            name = 'hse-' + os.urandom(8).hex()
            command = ['docker', 'run', '--name', name, '--network=none', '--read-only',
                       '--cap-drop=ALL', '--security-opt=no-new-privileges', '--pids-limit=64',
                       '--memory=256m', '--cpus=1', '--user=65534:65534',
                       '--tmpfs=/tmp:rw,nosuid,size=64m', '-v', f'{work}/hw:/input:ro',
                       '-w', '/tmp', image, 'python', '-I', '/checker.py', task['id']]
            try:
                code, output = bounded_run(command, timeout=20)
                if code != -1:
                    try:
                        inspected = subprocess.run(['docker','inspect','--format','{{json .State}}',name],
                                                   check=True,capture_output=True,text=True,timeout=10)
                        state = json.loads(inspected.stdout)
                    except (subprocess.SubprocessError,ValueError) as error:
                        raise RuntimeError('Cannot establish container execution status') from error
                    if state.get('Status') != 'exited' or state.get('Error'):
                        raise RuntimeError('Container infrastructure failed')
                if output == b'course-infrastructure-error\n':
                    raise RuntimeError('Test environment could not be prepared')
                passed = code == 0 and output == COMPLETED
                status = 'passed' if passed else 'failed'
            except subprocess.TimeoutExpired:
                passed, status = False, 'timeout'
            finally:
                subprocess.run(['docker','rm','-f',name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            results.append({'id':task['id'], 'status':status, 'points':task['points'] if passed else 0})
    return results


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--hw',required=True)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--trusted',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    hw=load_assignments(args.trusted)[args.hw]
    # Receipt time comes from GitHub, supplied by trusted workflow, never commit author time.
    created=os.environ['RUN_CREATED_AT']
    deadline=os.environ.get('COURSE_DEADLINE') or hw['deadline']
    limit=int(os.environ.get('COURSE_ATTEMPTS') or hw['attempts'])
    number=int(os.environ['GITHUB_RUN_NUMBER'])
    result={'schema':1,'homework':args.hw,'sha':os.environ['GITHUB_SHA'],
            'run_id':int(os.environ['GITHUB_RUN_ID']), 'run_number':number,
            'created_at':created,'grader_sha':os.environ['GRADER_SHA'],'tasks':[]}
    late=dt.datetime.fromisoformat(created.replace('Z','+00:00')) > dt.datetime.fromisoformat(deadline)
    if number > limit:
        result['status']='limit'
    else:
        with tempfile.TemporaryDirectory() as directory:
            context=Path(directory)/'grading'
            shutil.copytree(args.trusted/'Other/grading',context)
            (context/'requirements.txt').write_text('\n'.join(hw.get('dependencies',[]))+'\n')
            subprocess.run(['docker','build','-q','-t','hse-grading',str(context)],check=True)
        result['tasks']=execute(hw,args.source,args.trusted,'hse-grading')
        result['score']=round(min(10,sum(t['points'] for t in result['tasks'])),2)
        result['status']='late' if late else 'graded'
        result['credited_score']=0 if late else result['score']
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    labels={'graded':'Проверено','late':'Сдано после дедлайна. Итог за эту сдачу — 0 / 10.','limit':'Лимит попыток исчерпан'}
    lines=[f'## {hw["title"]}',labels[result['status']]]
    if result['status'] in ('graded','late'):
        if not late:lines.append(f'Попытка {number} / {limit}')
        lines += [f'Результат тестов: **{result["score"]} / 10**',f'Зачётный балл этой сдачи: **{result["credited_score"]} / 10**','', '| Задача | Балл | Статус |','|---|---:|---|']
        lines += [f'| {t["id"]} | {t["points"]} | {t["status"]} |' for t in result['tasks']]
    lines += ['', 'Официальная ведомость обновляется после проверки происхождения результата, раз в три часа.']
    Path(os.environ.get('GITHUB_STEP_SUMMARY',str(args.output/'summary.md'))).write_text('\n'.join(lines)+'\n')

if __name__=='__main__': main()
