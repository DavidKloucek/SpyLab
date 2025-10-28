import { defineConfig } from 'orval';

export default defineConfig({
    api: {
        input: 'http://localhost:8000/openapi.json',
        output: {
            target: 'src/api/generated.ts',
            client: "axios",
            prettier: true,
            override: {
                mutator: {
                    path: './src/api/orvalMutator.ts',
                    name: 'orvalMutator',
                },
            },
        },
    },
});
