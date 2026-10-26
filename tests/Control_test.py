#进入 pycharm终端 [Terminal] 命令行执行-> python .\tests\Control_test.py
import os
"""
test开头的都是测试类
运行所有测试类:pytest .\tests\test_api.py
运行指定的测试类:pytest .\tests\test_api.py::test_health
加上 -v参数可以查看输出
加上-s --alluredir report --clean-alluredir生成报告
生成报告后再运行allure generate ./report -o ./html_report --clean命令能产生allure报告
"""

#配置cmd下执行命令（生成allure执行命令）
testapi_cmd = "pytest -s --alluredir report --clean-alluredir ./tests/test_api.py -v"
testtools_cmd = "pytest -s --alluredir report --clean-alluredir ./tests/test_tools.py -v"
testutils_cmd = "pytest -s --alluredir report --clean-alluredir ./tests/test_utils.py -v"
make_htmlreport_cmd = "allure generate ./report -o ./html_report --clean"

lst = [testtools_cmd,make_htmlreport_cmd]
for item in lst:
    os.system(item)