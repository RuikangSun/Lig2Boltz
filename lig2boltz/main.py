"""
Lig2Boltz
Copyright (c) 2025 Sun Ruikang @ ShanghaiTech University
Licensed under the MIT License
Lig2Boltz是一个用于批量生成Boltz-2输入文件的脚本。基于template.yaml文件作为输入模版，根据input.txt（或.cxv)中的变量信息，生成多个Boltz-2输入文件，输出到outputDir目录下。随后，用户可以使用"boltz predict ./example/output --use_msa_server"指令预测整个output目录下的多个输入文件。
"""

import os
import csv
import re
import sys

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
        self.templateContent = self._loadTemplate()
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
        加载并返回YAML模板内容
        
        Returns:
            str: YAML模板内容
            
        Raises:
            IOError: 读取文件错误时抛出
        """
        try:
            with open(self.templatePath, 'r') as file:
                content = file.read()
                self._log(f"成功加载模板文件: {self.templatePath}")
                return content
        except Exception as e:
            raise IOError(f"读取模板文件错误: {e}")

    def _extractMarkers(self):
        """
        从模板中提取所有VARIANT标记
        
        Returns:
            list: 按数字排序的标记列表
        """
        markers = set(self.MARKER_PATTERN.findall(self.templateContent))
        markersList = sorted(markers, key=int)
        self._log(f"从模板中提取到 {len(markersList)} 个标记: {', '.join(f'<<VARIANT{m}>>' for m in markersList)}")
        return markersList

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
        
        successCount = 0
        for i, data in enumerate(inputData):
            try:
                # 准备替换值
                replacements = data if fileType == 'csv' else [data]
                
                # 创建替换后的内容
                content = self._replaceMarkers(self.templateContent, replacements)
                
                # 生成输出文件名
                outputFileName = f'{i + 1}.yaml'
                outputFilePath = os.path.join(self.outputDir, outputFileName)
                
                # 写入文件
                with open(outputFilePath, 'w') as file:
                    file.write(content)
                    
                successCount += 1
                self._log(f"成功生成: {outputFilePath}")
                
            except Exception as e:
                self._log(f"生成文件 {i+1} 时出错: {e}", file=sys.stderr)
                
        self._log(f"YAML文件生成完成，成功 {successCount} 个，失败 {len(inputData) - successCount} 个")
        return successCount

    def _replaceMarkers(self, content, values):
        """
        替换内容中的所有VARIANT标记为对应的值
        
        Args:
            content (str): 模板内容
            values (list): 用于替换标记的值列表
            
        Returns:
            str: 替换后的内容
        """
        def replaceMatch(match):
            """正则表达式替换回调函数"""
            variantIndex = int(match.group(1)) - 1
            if 0 <= variantIndex < len(values):
                return values[variantIndex]
            return match.group(0)  # 如果没有对应的值，保持标记不变
            
        return self.MARKER_PATTERN.sub(replaceMatch, content)


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
        successCount = generator.generateYamlFiles(inputData, fileType)
        
        if debug:
            print(f"所有YAML文件已生成到目录: {outputDir}")
            print(f"成功生成 {successCount} 个文件")
            
        return successCount
        
    except Exception as e:
        if debug:
            print(f"程序执行出错: {e}", file=sys.stderr)
        raise


# 主程序
if __name__ == "__main__":
    try:
        # 解析命令行参数以支持debug模式
        debugMode = '--debug' in sys.argv
        
        successCount = generateBoltzInputs(templatePath, inputPath, outputDir, debugMode)
        
        if debugMode and successCount > 0:
            print(f"成功生成 {successCount} 个YAML文件到目录: {outputDir}")
            
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)