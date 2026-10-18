# CLAUDE_MISSION_M62_PORTABLE_PACKAGE.md

**Mission:** Build a portable Windows bundle for AHOS with health script
**Mission ID:** M62
**Status:** NOT_STARTED
**Queue Position:** 2

## Task Description
Create a portable Windows bundle of AHOS that includes Python, Node.js, dependencies, a desktop shortcut, a data-move guide, and a post-move health check script. The bundle must be created in an isolated worktree, tested, and documented.

## Success Criteria
1. Portable bundle created in isolated worktree (no shared data between worktrees)
2. Bundle includes:
   - AHOS application code
   - Python with all required packages (from freeze_lane_a.py, requirements.txt)
   - Node.js with Next.js dependencies
   - Desktop shortcut launching the app
   - Data move guide for transferring between machines
   - Health check script that validates the bundle
3. Health script uses existing M70.1 probe (consumes it, doesn't duplicate)
4. Secrets stored in Windows Credential Manager by owner (no hardcoding)
5. Bundle tested on a clean machine (or documented test process)
6. Documentation created (README, installation guide, troubleshooting)

## Files to Create
- `G:\robat\ahos_m62_portable\` - isolated worktree for portable bundle
- `M62_PORTABLE_README.md` - bundle documentation
- `M62_INSTALL_GUIDE.md` - installation instructions
- `M62_HEALTH_SCRIPT.ps1` - post-move health validation
- `M62_DATA_MOVE_GUIDE.md` - instructions for transferring data

## Dependencies & Constraints
- Must use `freeze_lane_a.py` for frozen Python packages (Lane A frozen)
- Must use existing `M70.1` probe for health checking
- Must not duplicate M70.1 probe code
- Must NOT include secrets in bundle
- Must use Windows-only packaging (no Linux support in this iteration)
- Lane A frozen code in `discovery/` directory is read-only source

## Testing Strategy
1. Create bundle in worktree
2. Copy bundle to separate machine or isolated VM
3. Run health script
4. Verify all components are functional
5. Document any failures or edge cases

## Notes
- Secret restoration is owner-gated (Windows Credential Manager)
- Database files must be copied separately (data move guide required)
- Bundle should be small enough for typical portable use (not 100+ GB)
- Use 7-zip or similar for creating portable archive