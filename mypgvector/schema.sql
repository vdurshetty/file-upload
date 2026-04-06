-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create sample table if not exists
CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    item_data JSONB,
    embedding vector(1536) -- vector data
);