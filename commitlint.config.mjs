export default {
  extends: ['@commitlint/config-conventional'],
  ignores: [(commit) => /^wip/i.test(commit)],
  rules: {
    'scope-enum': [
      2,
      'always',
      ['agents', 'scripts', 'shell', 'terminal', 'git', 'tooling', 'repo'],
    ],
  },
};
