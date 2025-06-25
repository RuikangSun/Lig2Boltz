# Lig2Boltz


**Lig2Boltz是一个用于批量生成Boltz-2输入文件的脚本。**

## 运行

打开你最喜欢的集成开发环境，打开main.py，修改自定义参数，点击集成开发环境的运行功能。如果你是Python新手，请在生成式对话人工智能的帮助下，修改example文件夹内的自定义参数，执行“python .\lig2boltz\main.py --debug”命令，执行代码后，在.\example\output文件夹下，可以看到生成的文件。

## 自定义参数

1. 模板文件路径。使用诸如“<`<VARIANT1>`>”、“<`<VARIANT2>`>”格式作为变量。
2. 输入数据文件路径。可以是用txt或csv文件的路径。使用txt文件时，每行数据为json格式。使用txt文件时，每行对应一个变量（例如药物分子虚拟筛选场景下，每一行是不同的配体分子的SMILES）；使用csv文件时，每列对应“<`<VARIANT1>`>”、“<`<VARIANT2>`>”等变量（例如可用于研究不同配体分子的SMILES和不同蛋白的FASTA的多种结合模式）。
3. 输出目录。文件会按照input.txt（或.csv）的行数编号。


**Lig2Boltz is a script designed for the batch generation of input files for Boltz-2.**

## Execution

Open your favorite Integrated Development Environment (IDE), open main.py, modify the customizable parameters, and click the run function of the IDE. If you are new to Python, with the help of a generative conversational AI, please modify the customizable parameters in the example folder, execute the command python .\lig2boltz\main.py --debug. After running the code, you can find the generated files in the .\example\output folder.

## Customizable Parameters

1. **Template File Path**: Designate the path to your template file. Use placeholders such as `<<VARIANT1>>` and `<<VARIANT2>>` within the template to mark variable positions.
2. **Input Data File Path**: Specify the path to your input data, which can be in either TXT or CSV format.

   - **TXT Format**: Each line in the TXT file should be in JSON format. In scenarios like virtual screening of drug molecules, each line might contain the SMILES string of a different ligand molecule.
   - **CSV Format**: Each column in the CSV file corresponds to variables like `<<VARIANT1>>`, `<<VARIANT2>>`, etc. This format is useful for exploring various binding patterns, such as combinations of different ligand SMILES strings and different protein FASTA sequences.
3. **Output Directory**: Define the directory where the generated files will be saved. The output files will be numbered according to the rows in the input.txt (or.csv) file.
