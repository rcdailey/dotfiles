export default {
  extends: ['@commitlint/config-conventional'],
  ignores: [(commit) => /^wip/i.test(commit)],
  rules: {
    // Enforce 72 character line length for body
    'body-max-line-length': [2, 'always', 72],
    // Enforce 72 character line length for footer
    'footer-max-line-length': [2, 'always', 72],
    // Enforce 72 character subject line (more lenient than 50)
    'header-max-length': [2, 'always', 72],
  },
};
