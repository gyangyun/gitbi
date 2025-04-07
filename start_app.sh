#!/bin/bash

set -e

app_dir="$(realpath ./app)";

# 检查配置文件
if [ -n "$GITBI_CONFIG_PATH" ]; then
    echo "Using config file: $GITBI_CONFIG_PATH"
    if [ ! -f "$GITBI_CONFIG_PATH" ]; then
        echo "Config file not found: $GITBI_CONFIG_PATH"
        exit 1
    fi
    config_file="$GITBI_CONFIG_PATH"
else
    # 检查示例配置
    if [ ! -d "./gitbi-example" ]; then
        echo "Example repo not found, cloning..."
        git clone https://github.com/ppatrzyk/gitbi-example.git
    fi
    
    # 创建示例配置文件
    example_repo_dir="$(cd ./gitbi-example && pwd)"
    config_file="$example_repo_dir/example_config.yaml"
    cat > "$config_file" << EOF
# Gitbi 示例配置文件

# 仓库配置
repo:
  dir: $example_repo_dir

# 数据库配置
databases:
  pokemon:
    type: sqlite
    connection_string: "$example_repo_dir/pokemon.sqlite"
    
  shootings:
    type: duckdb
    connection_string: ":memory:"
    
  suicide:
    type: sqlite
    connection_string: "$example_repo_dir/suicide.sqlite"
EOF
    
    echo "Using example configuration"
    export GITBI_CONFIG_PATH="$config_file"
fi

# 从配置文件读取仓库路径
repo_dir=$(python3 -c "import yaml; f=open('$config_file'); print(yaml.safe_load(f)['repo']['dir']); f.close()")
if [ ! -d "$repo_dir" ]; then
    echo "Repository directory not found: $repo_dir"
    echo "Please update the config file with the correct repository path"
    exit 1
fi

cd "$repo_dir"

# 检查git仓库
inside_git_repo="$(git rev-parse --is-inside-work-tree)"
toplevel="$(git rev-parse --show-toplevel)"
if [ "$repo_dir" != "$toplevel" ]; then
    echo "Passed subdirectory of an existing git repo at $toplevel"
    exit 1
else
    past_commits=$(git log)
fi

echo "Git repo OK, starting gitbi..."
cd "$app_dir"
uvicorn \
    --host=0.0.0.0 \
    --port=8000 \
    --log-level=debug \
    --workers=1 \
    --app-dir="$app_dir" \
    main:app
