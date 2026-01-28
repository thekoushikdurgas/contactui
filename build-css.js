const { execSync } = require('child_process');

console.log('Building Tailwind CSS for production...');

try {
  execSync('npx tailwindcss -i ./static/css/tailwind.css -o ./static/css/built.css --minify', {
    stdio: 'inherit',
    cwd: __dirname
  });
  console.log('Build complete!');
} catch (error) {
  console.error('Build failed:', error.message);
  process.exit(1);
}