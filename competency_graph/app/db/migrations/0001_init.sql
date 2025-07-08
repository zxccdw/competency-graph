-- Пользователи системы
CREATE TABLE IF NOT EXISTS "user" (
    id SERIAL PRIMARY KEY,
    display_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE
);

-- Версии узлов графа
CREATE TABLE IF NOT EXISTS node_version (
    node_uri VARCHAR(255) PRIMARY KEY,
    version INTEGER NOT NULL DEFAULT 1,
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- История изменений узлов
CREATE TABLE IF NOT EXISTS node_change_history (
    id SERIAL PRIMARY KEY,
    node_uri VARCHAR(255) NOT NULL,
    user_id INTEGER REFERENCES "user"(id),
    change_type VARCHAR(50) NOT NULL, -- CREATE, UPDATE, DELETE
    old_value JSONB,
    new_value JSONB,
    version INTEGER NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_user_email ON "user"(email);
CREATE INDEX IF NOT EXISTS idx_node_version_uri ON node_version(node_uri);
CREATE INDEX IF NOT EXISTS idx_node_history_uri ON node_change_history(node_uri);
CREATE INDEX IF NOT EXISTS idx_node_history_user ON node_change_history(user_id);
