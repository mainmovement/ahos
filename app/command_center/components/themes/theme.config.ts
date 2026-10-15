/**
 * AHOS has exactly one theme. The ported template shipped ten switchable skins;
 * their CSS is not part of the port, so the list is collapsed to the one skin
 * that exists. Keeping the THEMES array (and its name/value shape) means the
 * theme selector and ActiveThemeProvider still work unchanged if a second skin
 * is ever added back alongside themes/ahos.css.
 */
export const DEFAULT_THEME = 'ahos';

export const THEMES = [
  {
    name: 'AHOS Command',
    value: 'ahos'
  }
];
