var chart_id = '{{ echart_id }}'
var current_data = null;
var initial_viz = true;
var saved_viz = null;

try {
    console.log('Parsing saved viz from template:', '{{ viz|safe }}');
    saved_viz = JSON.parse('{{ viz|safe }}');
    console.log('Parsed saved_viz:', saved_viz);
} catch (error) {
    console.error('Failed to parse saved viz:', error);
}

// 初始化下拉框选项
function initializeSelectOptions() {
    var select_ids = ['echart-options-xaxis', 'echart-options-yaxis', 'echart-options-zaxis', 'echart-options-group'];

    // 先设置一个默认选项
    select_ids.forEach(id => {
        var select = document.getElementById(id);
        if (select) {
            select.innerHTML = '<option value="_NONE">请选择</option>';
        }
    });

    // 如果有保存的配置，立即应用
    if (saved_viz) {
        console.log('Applying initial configuration:', saved_viz);
        // 设置图表类型
        var typeSelect = document.getElementById('echart-options-type');
        if (typeSelect && saved_viz.type) {
            typeSelect.value = saved_viz.type;
        }

        // 设置其他选项
        select_ids.forEach(id => {
            var select = document.getElementById(id);
            var key = id.replace('echart-options-', '');
            if (select && saved_viz[key]) {
                // 确保选项存在
                if (!select.querySelector(`option[value="${saved_viz[key]}"]`)) {
                    var option = document.createElement('option');
                    option.value = saved_viz[key];
                    option.textContent = saved_viz[key];
                    select.appendChild(option);
                }
                select.value = saved_viz[key];
            }
        });
    }
}

// 在页面加载完成后初始化选项
document.addEventListener('DOMContentLoaded', initializeSelectOptions);

function array_ident(arr1, arr2) {
    // https://stackoverflow.com/a/19746771
    return (arr1.length === arr2.length && arr1.every((value, index) => value === arr2[index]))
}
function get_chart_options() {
    var chart_options = {
        type: document.getElementById('echart-options-type').value,
        xaxis: document.getElementById('echart-options-xaxis').value,
        yaxis: document.getElementById('echart-options-yaxis').value,
        zaxis: document.getElementById('echart-options-zaxis').value,
        group: document.getElementById('echart-options-group').value,
    }
    console.log('Current chart options:', chart_options);
    return chart_options
}
window.get_chart_options = get_chart_options;
function update_chart_options() {
    console.log('Updating chart options, initial_viz:', initial_viz, 'saved_viz:', saved_viz);
    var select_ids = ['echart-options-xaxis', 'echart-options-yaxis', 'echart-options-zaxis', 'echart-options-group'];
    var headings = Array.from(document.getElementById(select_ids[0]).getElementsByTagName('option')).map((node) => node.value)
    var new_headings = ['_NONE'].concat(current_data.headings);

    if (!array_ident(headings, new_headings)) {
        console.log('Updating select options with new headings:', new_headings);
        select_ids.forEach(id => {
            var select = document.getElementById(id);
            if (select) {
                var currentValue = select.value; // 保存当前选中的值

                // 创建新的选项
                var columns = new_headings.map((name) => {
                    var entry = document.createElement("option");
                    entry.setAttribute('value', name);
                    entry.innerText = name;
                    return entry;
                });

                // 更新选项
                select.replaceChildren(...columns);

                // 如果是首次加载且有保存的配置
                if (initial_viz && saved_viz && saved_viz[id.replace('echart-options-', '')]) {
                    select.value = saved_viz[id.replace('echart-options-', '')];
                } else {
                    // 否则尝试恢复之前选中的值，如果不存在则使用默认值
                    select.value = new_headings.includes(currentValue) ? currentValue : '_NONE';
                }
            }
        });

        if (initial_viz && saved_viz) {
            initial_viz = false;
            console.log('Applying saved configuration:', saved_viz);
            // 应用图表类型
            var typeSelect = document.getElementById('echart-options-type');
            if (typeSelect && saved_viz.type) {
                typeSelect.value = saved_viz.type;
            }
        }
    }
}
function make_viz() {
    // this function wraps viz creation for query page
    try {
        var chart_el = document.getElementById(chart_id);
        var chart_options = get_chart_options();
        if (current_data === null || current_data.data.length === 0) {
            document.getElementById('echart-note').classList.remove("hidden");
            document.getElementById('echart-chart').classList.add("hidden");
            throw new Error('no data available');
        } else {
            document.getElementById('echart-note').classList.add("hidden");
            document.getElementById('echart-chart').classList.remove("hidden");
            create_viz(current_data, chart_options, chart_el);
        }
    } catch (error) {
        console.error(`Failed to draw chart`);
        console.error(error);
        alert(error)
    }
}
