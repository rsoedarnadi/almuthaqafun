// js/tools.js
// Receives tool_calls_executed from the agent response
// and routes each one to the correct frontend module.
// Add your Three.js hooks here as TODO comments get filled in.

import { transitionToScene } from './transition.js';

export function handleToolCalls(tools) {
  if (!tools || tools.length === 0) return;

  for (const tool of tools) {
    console.log(`[TOOL] ${tool.name}`, tool.args);

    switch (tool.name) {

      case "transition_scene":
        // Small delay so TTS reply finishes before the fade starts
        setTimeout(() => transitionToScene(tool.args.scene_id), 600);
        break;

      case "trigger_animation":
        // TODO: your friend calls their NPC animation system here
        // e.g. NPCController.play(tool.args.animation);
        console.log(`[animation] ${tool.args.animation}`);
        break;

      case "open_ui":
        // TODO: show the relevant UI overlay
        // e.g. UIManager.open(tool.args.panel);
        console.log(`[ui] open panel: ${tool.args.panel}`);
        break;

      case "award_badge":
        // TODO: show badge award screen
        // e.g. BadgeUI.show(tool.args.badge_title, tool.args.congratulations);
        console.log(`[badge] ${tool.args.badge_title}`);
        break;

      case "explore_object":
        // TODO: highlight the object in the Three.js scene
        // e.g. SceneManager.highlight(tool.args.object_id);
        console.log(`[explore] ${tool.args.object_id}`);
        break;

      case "give_directions":
        // TODO: show a waypoint arrow in the scene
        // e.g. WaypointUI.show(tool.args.destination);
        console.log(`[directions] to: ${tool.args.destination}`);
        break;

      default:
        console.warn(`[TOOL] Unknown tool: ${tool.name}`);
    }
  }
}
