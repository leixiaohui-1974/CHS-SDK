import JSZip from 'jszip';
import { saveAs } from 'file-saver';
import yaml from 'js-yaml';

/**
 * Takes the project configuration state and exports it as a zip file
 * containing the relevant YAML configuration files.
 *
 * @param projectConfig The project configuration object from the Zustand store.
 */
export const exportProjectAsZip = async (projectConfig: any) => {
  if (!projectConfig) {
    console.error("Export failed: projectConfig is null.");
    return;
  }

  try {
    const zip = new JSZip();

    // 1. Create components.yml
    // The backend expects a list of components under a 'components' key.
    // However, our internal state is just the list. We need to wrap it.
    if (projectConfig.components) {
      // We need to remove the internal '_id' from connections before exporting
      const cleanComponents = projectConfig.components.map((c: any) => {
        const { ...rest } = c;
        // In the future, we might add internal state to components too.
        // This is where we would clean it up.
        return rest;
      });
      zip.file('components.yml', yaml.dump({ components: cleanComponents }));
    }

    // 2. Create topology.yml
    if (projectConfig.topology) {
       const cleanConnections = projectConfig.topology.connections.map((c: any) => {
        const { _id, ...rest } = c; // Remove internal _id before saving
        return rest;
      });
      const topologyData = {
        ...projectConfig.topology,
        connections: cleanConnections,
      }
      zip.file('topology.yml', yaml.dump(topologyData));
    }

    // 3. Create agents.yml (if it exists)
    if (projectConfig.agents) {
      zip.file('agents.yml', yaml.dump(projectConfig.agents));
    }

    // 4. Create other config files if they exist (e.g., config.yml, output.yml)
    // For now, we are only handling the core files.

    // Generate the zip file and trigger a download
    const zipBlob = await zip.generateAsync({ type: 'blob' });
    const projectName = projectConfig.name || 'project';
    saveAs(zipBlob, `${projectName}.zip`);

  } catch (error) {
    console.error("Failed to export project:", error);
    // Optionally, show a message to the user
  }
};
