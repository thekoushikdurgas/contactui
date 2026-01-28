module.exports = {
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/static/js'],
  testMatch: ['**/__tests__/**/*.test.js', '**/?(*.)+(spec|test).js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/static/js/$1',
  },
  setupFilesAfterEnv: ['<rootDir>/static/js/__tests__/setup.js'],
  collectCoverageFrom: [
    'static/js/**/*.js',
    '!static/js/**/*.min.js',
    '!static/js/__tests__/**',
  ],
  coverageDirectory: 'coverage/js',
  verbose: true,
};
