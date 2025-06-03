module.exports = {
  courtlistener: { // Using 'courtlistener' as the key for this configuration
    input: {
      // Assuming the latest generated OpenAPI schema is at the root.
      // Adjust if it's consistently placed elsewhere (e.g., a 'docs' folder)
      // by the generate_openapi_yaml command.
      target: './openapi-v4-refined-pass2.yaml',
    },
    output: {
      // Output directory for the SDK
      target: './sdk/courtlistener-api/src', // Main generated files here
      schemas: './sdk/courtlistener-api/src/schemas', // Generated type schemas here
      client: 'fetch', // Use the Fetch client
      mode: 'tags-split', // Split files by tags, good for large APIs
      baseUrl: '/api/rest/v4', // Default base URL for the v4 API. This might need adjustment or to be made configurable at runtime by the SDK user.
      override: {
        mutator: { // Custom mutator to potentially handle base URL or request options
          path: './sdk/courtlistener-api/custom-instance.ts', // Path to a custom fetch instance
          name: 'customInstance', // Name of the exported function/instance
        },
      },
    },
    hooks: { // Optional: hooks for post-processing, e.g., running Prettier
      afterAllFilesWrite: 'prettier --write ./sdk/courtlistener-api/src',
    }
  }
};
