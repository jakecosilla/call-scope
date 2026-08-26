import { execFileSync } from 'node:child_process';

function run(command, args) {
  execFileSync(command, args, {
    stdio: 'inherit',
    shell: process.platform === 'win32',
  });
}

run('npm', ['ls', 'vite', 'vitest', '@vitejs/plugin-react', '@playwright/test']);
run('npm', ['run', 'typecheck']);
run('npm', ['run', 'lint']);
run('npm', ['run', 'test']);
run('npm', ['run', 'build']);
