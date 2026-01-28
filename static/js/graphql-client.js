// GraphQL Client for Django DocsAI App

class GraphQLClient {
    constructor(endpoint, apiKey) {
        this.endpoint = endpoint || '/graphql';
        this.apiKey = apiKey || '';
    }

    async executeQuery(query, variables = {}) {
        try {
            const response = await fetch(this.endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    ...(this.apiKey && { 'Authorization': `Bearer ${this.apiKey}` })
                },
                body: JSON.stringify({
                    query,
                    variables
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.errors) {
                throw new Error(result.errors.map(e => e.message).join(', '));
            }

            return result.data;
        } catch (error) {
            console.error('GraphQL query error:', error);
            throw error;
        }
    }

    async executeMutation(mutation, variables = {}) {
        return this.executeQuery(mutation, variables);
    }
}

// Initialize global GraphQL client
window.graphql = new GraphQLClient(
    window.GRAPHQL_ENDPOINT || 'http://localhost:8000/graphql',
    window.GRAPHQL_API_KEY || ''
);
