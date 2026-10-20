// ESLint settings for static/js/main.js (browser script; Bootstrap is a global).
// Run: npm i --no-save eslint@9.17.0 @eslint/js@9.17.0 globals@15.14.0 && npx eslint static/js
import js from "@eslint/js";
import globals from "globals";
export default [js.configs.recommended, {languageOptions: {ecmaVersion: 2022, sourceType: "script", globals: {...globals.browser, bootstrap: "readonly"}}}];
