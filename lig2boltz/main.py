"""
Lig2Boltz
Copyright (c) 2025 Sun Ruikang @ ShanghaiTech University
Licensed under the MIT License
Lig2Boltz是一个用于批量生成Boltz-2输入文件的脚本。基于template.yaml文件作为输入模版，根据input.txt（或.cxv)中的变量信息，生成多个Boltz-2输入文件，输出到outputDir目录下。随后，用户可以使用“boltz predict ./example/output --use_msa_server”指令预测整个output目录下的多个输入文件。
"""

import os
import csv
import re
import sys
import json

# 用户需要修改的路径和参数
templatePath = './example/template.yaml'
inputPath = './example/input.txt'  # 可以是txt或csv文件路径
outputDir = './example/output'

class YamlGenerator:
    """YAML文件生成器，用于根据模板和输入数据批量生成YAML文件"""
    
    MARKER_PATTERN = re.compile(r'<<VARIANT(\d+)>>')
    
    def __init__(self, templatePath, outputDir, debug=False):
        """
        初始化YamlGenerator类
        
        Args:
            templatePath (str): 空白模板文件的路径
            outputDir (str): 生成的YAML文件的输出目录
            debug (bool, optional): 是否启用调试模式，默认不启用
            
        Raises:
            FileNotFoundError: 模板文件不存在时抛出
            ValueError: 模板文件不是YAML格式时抛出
        """
        self.templatePath = templatePath
        self.outputDir = outputDir
        self.debug = debug
        
        # 验证并准备模板文件
        self._validateTemplatePath()
        self.template = self._loadTemplate()
        self.markers = self._extractMarkers()
        
        # 确保输出目录存在
        self._ensureOutputDirExists()
        
        # 打印调试信息
        self._log(f"初始化YAML生成器: 模板={self.templatePath}, 输出目录={self.outputDir}")

    def _log(self, message):
        """根据debug模式决定是否打印信息"""
        if self.debug:
            print(message)

    def _validateTemplatePath(self):
        """
        验证模板文件是否存在且为yaml文件
        
        Raises:
            FileNotFoundError: 模板文件不存在时抛出
            ValueError: 模板文件不是YAML格式时抛出
        """
        if not os.path.exists(self.templatePath):
            raise FileNotFoundError(f"模板文件不存在: {self.templatePath}")
        if not self.templatePath.lower().endswith(('.yaml', '.yml')):
            raise ValueError(f"模板文件必须是YAML格式: {self.templatePath}")

    def _loadTemplate(self):
        """
        加载并返回YAML模板
        
        Returns:
            dict: 解析后的YAML模板数据
            
        Raises:
            ValueError: YAML模板解析错误时抛出
        """
        try:
            with open(self.templatePath, 'r') as file:
                content = file.read()
                # 尝试将YAML转换为Python字典
                # 注意：这是一个简化的实现，不支持所有YAML特性
                self._log(f"成功加载模板文件: {self.templatePath}")
                return self._yaml_to_dict(content)
        except Exception as e:
            raise ValueError(f"YAML模板解析错误: {e}")

    def _yaml_to_dict(self, yaml_str):
        """
        将简化的YAML字符串转换为字典
        
        注意：这是一个简化的实现，仅支持:分隔的键值对和简单的嵌套结构
        不支持复杂的YAML特性如引用、标签等
        
        Args:
            yaml_str (str): YAML格式的字符串
            
        Returns:
            dict: 转换后的字典
        """
        data = {}
        lines = yaml_str.split('\n')
        current_indent = 0
        current_dict = data
        parent_dicts = []
        
        for line in lines:
            # 跳过空行和注释
            if not line.strip() or line.strip().startswith('#'):
                continue
                
            # 计算缩进
            indent = len(line) - len(line.lstrip())
            
            # 处理缩进变化
            if indent > current_indent:
                parent_dicts.append(current_dict)
                current_dict = current_dict[last_key]
                current_indent = indent
            elif indent < current_indent:
                while indent < current_indent and parent_dicts:
                    current_dict = parent_dicts.pop()
                    current_indent = len(line) - len(line.lstrip()) if line.strip() else 0
            
            # 提取键值对
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # 处理嵌套结构
                if value == '':
                    current_dict[key] = {}
                    last_key = key
                else:
                    # 尝试解析值的类型
                    try:
                        value = json.loads(value)
                    except:
                        pass  # 保持为字符串
                    current_dict[key] = value
                    
        return data

    def _dict_to_yaml(self, data, indent=0):
        """
        将字典转换为YAML格式的字符串
        
        Args:
            data (dict): 要转换的字典
            indent (int): 当前缩进级别
            
        Returns:
            str: YAML格式的字符串
        """
        yaml_str = ''
        indent_str = ' ' * (indent + 2)  # 修复了此处的indent_str定义
        
        for key, value in data.items():
            prefix = ' ' * indent
            
            if isinstance(value, dict):
                yaml_str += f"{prefix}{key}:\n"
                yaml_str += self._dict_to_yaml(value, indent + 2)
                
            elif isinstance(value, list):
                yaml_str += f"{prefix}{key}:\n"
                for item in value:
                    if isinstance(item, dict):
                        yaml_str += f"{prefix}  - \n"
                        yaml_str += self._dict_to_yaml(item, indent + 4)
                    else:
                        yaml_str += f"{prefix}  - {item}\n"
                        
            else:
                # 处理特殊字符
                if isinstance(value, str):
                    # 处理包含换行符的字符串
                    if '\n' in value:
                        lines = [indent_str + line for line in value.split('\n')]
                        value = f'|-\n{"".join(lines)}'
                    # 处理包含冒号的字符串
                    elif ':' in value and not value.startswith(('{', '[', '"', "'")):
                        value = f'"{value}"'  # 用引号包裹
                        
                yaml_str += f"{prefix}{key}: {value}\n"
                
        return yaml_str

    def _extractMarkers(self):
        """
        从模板中提取所有VARIANT标记
        
        Returns:
            list: 按数字排序的标记列表
        """
        markers = set()
        
        def findMarkers(data):
            """递归查找数据中的所有标记"""
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, str):
                        markers.update(self.MARKER_PATTERN.findall(value))
                    findMarkers(value)
            elif isinstance(data, list):
                for item in data:
                    findMarkers(item)
        
        findMarkers(self.template)
        markers_list = sorted(markers, key=int)
        self._log(f"从模板中提取到 {len(markers_list)} 个标记: {', '.join(f'<<VARIANT{m}>>' for m in markers_list)}")
        return markers_list

    def _ensureOutputDirExists(self):
        """
        确保输出目录存在，如果不存在则创建
        """
        if not os.path.exists(self.outputDir):
            os.makedirs(self.outputDir, exist_ok=True)
            self._log(f"创建输出目录: {self.outputDir}")
        else:
            self._log(f"输出目录已存在: {self.outputDir}")

    def readInputFile(self, inputPath):
        """
        读取输入文件，自动检测文件类型
        
        Args:
            inputPath (str): 输入文件的路径
            
        Returns:
            tuple: 包含两个元素的元组：
                - list: 输入数据列表
                - str: 文件类型 ('txt' 或 'csv')
                
        Raises:
            FileNotFoundError: 输入文件不存在时抛出
            ValueError: 文件类型不支持时抛出或文件为空时抛出
        """
        if not os.path.exists(inputPath):
            raise FileNotFoundError(f"输入文件不存在: {inputPath}")
            
        fileExtension = os.path.splitext(inputPath)[1].lower()
        inputData = []
        
        if fileExtension == '.txt':
            with open(inputPath, 'r') as file:
                inputData = [line.strip() for line in file if line.strip()]
            fileType = 'txt'
            self._log(f"以txt格式读取输入文件: {inputPath}, 共 {len(inputData)} 条记录")
        elif fileExtension == '.csv':
            with open(inputPath, 'r') as file:
                reader = csv.reader(file)
                inputData = [row for row in reader if any(field.strip() for field in row)]
            fileType = 'csv'
            self._log(f"以csv格式读取输入文件: {inputPath}, 共 {len(inputData)} 条记录")
        else:
            raise ValueError(f"不支持的文件类型: {fileExtension}，请使用.txt或.csv文件")
            
        if not inputData:
            raise ValueError(f"输入文件为空: {inputPath}")
            
        return inputData, fileType

    def generateYamlFiles(self, inputData, fileType):
        """
        根据输入数据生成YAML文件
        
        Args:
            inputData (list): 输入数据列表
            fileType (str): 文件类型 ('txt' 或 'csv')
            
        Raises:
            ValueError: 模板中没有找到任何标记或标记数量不足时抛出
        """
        # 确定所需的标记数量
        requiredMarkers = 1 if fileType == 'txt' else max(len(row) for row in inputData)
        
        # 验证模板中的标记是否足够
        if not self.markers:
            raise ValueError("模板中未找到任何VARIANT标记 (<<VARIANT1>>, <<VARIANT2>>, ...)")
            
        if int(self.markers[-1]) < requiredMarkers:
            raise ValueError(f"模板中标记不足，需要至少 {requiredMarkers} 个标记，但只找到 {len(self.markers)} 个")
            
        self._log(f"模板中发现标记: {', '.join(f'<<VARIANT{m}>>' for m in self.markers)}")
        self._log(f"开始生成YAML文件，共 {len(inputData)} 个")
        
        success_count = 0
        for i, data in enumerate(inputData):
            try:
                newTemplate = self._deepCopyDict(self.template)
                
                # 准备替换值
                replacements = data if fileType == 'csv' else [data]
                
                # 替换所有标记
                self._replaceMarkersInDict(newTemplate, replacements)
                
                # 生成输出文件名
                outputFileName = f'{i + 1}.yaml'
                outputFilePath = os.path.join(self.outputDir, outputFileName)
                
                # 将字典转换为YAML并写入文件
                yaml_content = self._dict_to_yaml(newTemplate)
                with open(outputFilePath, 'w') as file:
                    file.write(yaml_content)
                    
                success_count += 1
                self._log(f"成功生成: {outputFilePath}")
                
            except Exception as e:
                self._log(f"生成文件 {i+1} 时出错: {e}", file=sys.stderr)
                
        self._log(f"YAML文件生成完成，成功 {success_count} 个，失败 {len(inputData) - success_count} 个")
        return success_count

    def _deepCopyDict(self, original):
        """
        深度复制字典，避免修改原始模板
        
        Args:
            original (dict or list): 要复制的原始数据
            
        Returns:
            dict or list: 深拷贝后的对象
        """
        if isinstance(original, dict):
            return {k: self._deepCopyDict(v) for k, v in original.items()}
        elif isinstance(original, list):
            return [self._deepCopyDict(v) for v in original]
        else:
            return original

    def _replaceMarkersInDict(self, targetDict, values):
        """
        递归替换字典中所有VARIANT标记为对应的值
        
        Args:
            targetDict (dict or list): 要处理的目标字典或列表
            values (list): 用于替换标记的值列表
        """
        if isinstance(targetDict, dict):
            for key, value in targetDict.items():
                if isinstance(value, str):
                    targetDict[key] = self._replaceMarkersInString(value, values)
                else:
                    self._replaceMarkersInDict(value, values)
        elif isinstance(targetDict, list):
            for i, item in enumerate(targetDict):
                if isinstance(item, str):
                    targetDict[i] = self._replaceMarkersInString(item, values)
                else:
                    self._replaceMarkersInDict(item, values)

    def _replaceMarkersInString(self, s, values):
        """
        替换字符串中的VARIANT标记为对应的值
        
        Args:
            s (str): 要处理的字符串
            values (list): 用于替换标记的值列表
            
        Returns:
            str: 替换后的字符串
        """
        def replaceMatch(match):
            """正则表达式替换回调函数"""
            variantIndex = int(match.group(1)) - 1
            if 0 <= variantIndex < len(values):
                return values[variantIndex]
            return match.group(0)  # 如果没有对应的值，保持标记不变
            
        return self.MARKER_PATTERN.sub(replaceMatch, s)


def generateBoltzInputs(templatePath, inputPath, outputDir, debug=False):
    """
    生成Boltz-2的输入YAML文件
    
    Args:
        templatePath (str): 模板文件路径
        inputPath (str): 输入数据文件路径
        outputDir (str): 输出目录路径
        debug (bool, optional): 是否启用调试模式，默认不启用
        
    Returns:
        int: 成功生成的文件数量
    """
    try:
        if debug:
            print(f"开始生成YAML文件...")
        
        # 初始化生成器
        generator = YamlGenerator(templatePath, outputDir, debug)
        
        # 读取输入数据
        inputData, fileType = generator.readInputFile(inputPath)
        
        if debug:
            print(f"已读取 {len(inputData)} 条记录，文件类型: {fileType}")
        
        # 生成YAML文件
        success_count = generator.generateYamlFiles(inputData, fileType)
        
        if debug:
            print(f"所有YAML文件已生成到目录: {outputDir}")
            print(f"成功生成 {success_count} 个文件")
            
        return success_count
        
    except Exception as e:
        if debug:
            print(f"程序执行出错: {e}", file=sys.stderr)
        raise


# 主程序
if __name__ == "__main__":
    try:
        # 解析命令行参数以支持debug模式
        debugMode = '--debug' in sys.argv
        
        success_count = generateBoltzInputs(templatePath, inputPath, outputDir, debugMode)
        
        if debugMode and success_count > 0:
            print(f"成功生成 {success_count} 个YAML文件到目录: {outputDir}")
            
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
