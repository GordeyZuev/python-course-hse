"""Trusted host-side runner. Student code executes only inside disposable containers."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


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
            command = ['docker', 'run', '--name', name, '--rm', '--network=none', '--read-only',
                       '--cap-drop=ALL', '--security-opt=no-new-privileges', '--pids-limit=64',
                       '--memory=256m', '--cpus=1', '--user=65534:65534',
                       '--tmpfs=/tmp:rw,nosuid,size=64m', '-v', f'{work}/hw:/input:ro',
                       '-w', '/tmp', image, 'python', '-I', '-c',
                       'import shutil,os,runpy; shutil.copytree("/input","/tmp/hw"); '
                       f'os.chdir("/tmp/hw/{task["id"]}"); '
                       'import sys; sys.path.insert(0,os.getcwd()); runpy.run_path("test.py",run_name="__main__")']
            # Bound disk/log usage too; never forward arbitrary student output to GitHub.
            try:
                completed = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
                if completed.returncode in (125,126,127):
                    raise RuntimeError('Container infrastructure failed')
                passed = completed.returncode == 0
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
    hw=json.loads((args.trusted/'Other/tools/assignments.json').read_text())[args.hw]
    # Receipt time comes from GitHub, supplied by trusted workflow, never commit author time.
    created=os.environ['RUN_CREATED_AT']
    deadline=os.environ.get('COURSE_DEADLINE') or hw['deadline']
    limit=int(os.environ.get('COURSE_ATTEMPTS') or hw['attempts'])
    number=int(os.environ['GITHUB_RUN_NUMBER'])
    result={'schema':1,'homework':args.hw,'sha':os.environ['GITHUB_SHA'],
            'run_id':int(os.environ['GITHUB_RUN_ID']), 'run_number':number,
            'created_at':created,'grader_sha':os.environ['GRADER_SHA'],'tasks':[]}
    if dt.datetime.fromisoformat(created.replace('Z','+00:00')) > dt.datetime.fromisoformat(deadline):
        result['status']='late'
    elif number > limit:
        result['status']='limit'
    else:
        subprocess.run(['docker','build','-q','-t','hse-grading',str(args.trusted/'Other/grading')],check=True)
        result['tasks']=execute(hw,args.source,args.trusted,'hse-grading')
        result['score']=round(min(10,sum(t['points'] for t in result['tasks'])),2)
        result['status']='graded'
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    lines=[f'## {hw["title"]}',f'Статус: {result["status"]}',f'Попытка {number} / {limit}']
    if result['status']=='graded':
        lines += [f'Балл за эту сдачу: **{result["score"]} / 10**','', '| Задача | Балл | Статус |','|---|---:|---|']
        lines += [f'| {t["id"]} | {t["points"]} | {t["status"]} |' for t in result['tasks']]
    lines += ['', 'Официальная ведомость обновляется после проверки происхождения результата, раз в три часа.']
    Path(os.environ.get('GITHUB_STEP_SUMMARY',str(args.output/'summary.md'))).write_text('\n'.join(lines)+'\n')

if __name__=='__main__': main()
