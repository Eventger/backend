// Los títulos de PR deben validarse incluso si parecen merges automáticos.
module.exports = {
  ...require('../commitlint.config.cjs'),
  defaultIgnores: false,
};
