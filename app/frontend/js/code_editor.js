import { CodeJar } from '{{ request.app.url_path_for("static", path="/js/codejar.min.js") }}'
import hljs from '{{ request.app.url_path_for("static", path="/js/highlight/core.min.js") }}'
import sql from '{{ request.app.url_path_for("static", path="/js/highlight/sql.min.js") }}'
hljs.configure({ ignoreUnescapedHTML: true });
hljs.registerLanguage('sql', sql);

const editor = document.querySelector('.code-editor');
const jar = CodeJar(editor, (editor) => {
    editor.textContent = editor.textContent;
    hljs.highlightElement(editor);
});

function extractVariables(query) {
    // 匹配包括引号内的变量
    console.log('Query:', query); // 调试：打印原始查询
    const regex = /\{\{([^:}]+)(?::([^}]+))?\}\}/g;
    const variables = {};
    let match;

    while ((match = regex.exec(query)) !== null) {
        const [_, name, defaultValue = ''] = match;
        // 去除可能存在的引号
        const cleanDefaultValue = defaultValue.replace(/["']/g, '');
        variables[name] = cleanDefaultValue;
    }

    console.log('Variables:', variables); // 调试：打印提取的变量
    return variables;
}

function updateVariableInputs() {
    const query = jar.toString();
    const variables = extractVariables(query);
    const container = document.getElementById('variables-container');
    container.innerHTML = '';

    for (const [name, defaultValue] of Object.entries(variables)) {
        const row = document.createElement('div');
        row.className = 'variable-row';
        row.innerHTML = `
            <div class="variable-name">${name}</div>
            <input type="text" class="variable-value pure-input" data-var-name="${name}" value="${defaultValue}">
        `;
        container.appendChild(row);
    }
}

function getVariables() {
    const variables = {};
    document.querySelectorAll('.variable-value').forEach(input => {
        const name = input.dataset.varName;
        const value = input.value;
        variables[name] = value;
    });
    return variables;
}

function replaceVariables(query, variables) {
    let result = query;
    for (const [name, value] of Object.entries(variables)) {
        const regex = new RegExp('\\{\\{' + name + '(?::[^}]+)?\\}\\}', 'g');
        result = result.replace(regex, value);
    }
    return result;
}

// 用于执行查询的格式化函数
window.execute_query_format = function () {
    const query = jar.toString();
    const fileName = document.getElementById('file-name').value;
    const format = document.getElementById('result-format').value;
    const variables = getVariables();

    // 替换变量，生成最终的SQL
    const finalQuery = replaceVariables(query, variables);

    // 获取可视化配置
    const viz = window.get_chart_options ? JSON.stringify(window.get_chart_options()) : 'null';
    const echart_id = document.querySelector('#echart-chart div[id^="echart-"]')?.id || '';

    return JSON.stringify({
        query: finalQuery,
        file: fileName,
        format: format,
        viz: viz,
        echart_id: echart_id
    });
}

// 用于保存查询的格式化函数
window.save_query_format = function () {
    const query = jar.toString();  // 获取原始SQL模板
    const fileName = document.getElementById('file-name').value;
    const format = document.getElementById('result-format').value;

    // 获取可视化配置
    const viz = window.get_chart_options ? JSON.stringify(window.get_chart_options()) : 'null';
    const echart_id = document.querySelector('#echart-chart div[id^="echart-"]')?.id || '';

    console.log('save_query_format');
    console.log(query, fileName, format, viz, echart_id);
    return JSON.stringify({
        query: query,  // 保存原始SQL模板
        file: fileName,
        format: format,
        viz: viz,
        echart_id: echart_id
    });
}

// 监听编辑器内容变化，更新变量输入框
jar.onUpdate(() => {
    updateVariableInputs();
});

// 初始化变量输入框
updateVariableInputs();

function generate_link() {
    var data = JSON.parse(save_query_format());  // 使用原始SQL模板生成链接
    delete data.echart_id;
    var path = window.location.pathname.split("/").slice(0, 3).join("/");
    var query = "?";
    for (let [key, value] of Object.entries(data)) {
        query += `${encodeURIComponent(key)}=${encodeURIComponent(value)}&`;
    }
    var url = `${window.location.origin}${path}${query}`;
    alert(url);
}
window.generate_link = generate_link;