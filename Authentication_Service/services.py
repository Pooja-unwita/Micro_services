SERVICES = {
    "configuration_service": {
        "secret": "service-b-super-secret-key-that-is-long-and-secure",
        "audience": "my-app-audience",
        "scope": "read:embeddings"
    },
    "embedding_service": {
        "secret": "secret_keyy",
        "audience": "my-app-audience",
        "scope": "read:embeddings write:embeddings"
    }
}