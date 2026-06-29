# Update Opencode and Oh-My-OpenAgent Plugin


1. update opencode along with omo plugin. Depending on platform and available binaries, prefer `bunx` over `npx`, and prompt installation if neither exists. 

2. Update opencode via `opencode upgrade` and ensure the binary is in users path, and the updated .*rc file is updated to permenanttly add that to path if it doesn't exist. 

3. Run `bunx oh-my-openagent@latest doctor` and fix any warnings or errors that pop up 

4. After updating, run a quick smoke test via `opencode --version` and `bunx oh-my-openagent@latest version` to ensure the changes and updates have been picked up
