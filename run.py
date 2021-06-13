import psutil, os, configparser, atexit, shutil, dotenv

#Declaracao de variaveis globais
endString = "\n\nPrograma finalizado!\nBye Bye :)\n"
thisFilePath = str(os.path.dirname(os.path.realpath(__file__)))
tempDir1 = ""
tempDir2 = ""
#Vai para o diretorio atual do arquivo
os.chdir( thisFilePath )

#Plotting control vars and envs
plottingStarted = False
plotCountEnvName = "nOfPlots"
if not os.path.exists(thisFilePath+"\\.env"):
    open(thisFilePath+"\\.env", 'w').close()
envConf = dotenv.dotenv_values(".env")

#Pega o total de cpus logicas do pc
totalThreads = psutil.cpu_count()
#Cria o objeto de configuracao do arquivo ini
configParserObj = configparser.ConfigParser()
configParserObj.read("config.ini")
config = configParserObj["CHIA"]

#Funcao exit com wait de input
def tExit():
    input("Pressione 'Enter' para sair...")
    exit()

def setEnv(key, value):
    global envConf
    dotenv.set_key(".env", key, value)
    envConf = dotenv.dotenv_values(".env")

def getEnv(key):
    global envConf
    envConf = dotenv.dotenv_values(".env")
    if key in envConf:
        return envConf[key]
    else:
        return None

def plotEnv(op):
    if plotCountEnvName not in envConf:
        setEnv(plotCountEnvName, "0")
    plotEnvCount = int(getEnv(plotCountEnvName))

    def sum():
        setEnv(plotCountEnvName, str(plotEnvCount+1))
    def sub():
        if int(getEnv(plotCountEnvName)) > 0:
            setEnv(plotCountEnvName, str(plotEnvCount-1))

    ops = {
        'sum': sum,
        'sub': sub
    }
    func = ops.get(op)
    return func()

#Funcao de limpeza de diretorios
def cleanDir(path):
    dir = os.listdir(path)
    for file in dir:
        os.remove(path+"\\"+file)

#Funcao de acoes para usar tempdir
def createTempDir(path):
    try:
        if not os.path.exists(path):
            os.makedirs(path)
        else:
            cleanDir(path)
    except Exception as e:
        print("Nao foi possivel criar pastas temporarias!"+endString)
        tExit()

#Funcao de remocao de diretorios
def removeDir(path):
    shutil.rmtree(path, ignore_errors=True)

#Funcao para remover os diretorios temporarios
def removeTempDirs():
    try:
        global plottingStarted
        if(plottingStarted):
            print("\nDeletando diretorios temporarios")
            removeDir(tempDir1)
            removeDir(tempDir2)
        else:
            print("Nao foi necessario deletar diretorios")
    except Exception as e:
        print("\nNão conseguiu deletar os diretorios temporarios, Excecao:\n"+ str(e) + endString)

#Funcao para iniciar a plotagem
def startMadMaxPlotter():
    #Acessa dentro da funcao as variaveis globais
    global plottingStarted
    global tempDir1
    global tempDir2

    #Define o plot na env var para mais um e cria os diretorios temporarios
    plottingStarted = True
    plotEnv('sum')
    plotNumber = getEnv(plotCountEnvName)
    tempDir1 = config["temp.dir"]+"plot"+plotNumber+"Temp1\\"
    tempDir2 = config["temp.dir"]+"plot"+plotNumber+"Temp2\\"
    createTempDir(tempDir1)
    createTempDir(tempDir2)

    commandString = '" powershell \".\chia_plot -n \''+ config["plots"]+'\' -r \''+ str(totalThreads) +'\' -t \''+ tempDir1 +'\' -2 \''+ tempDir2 +'\' -d \''+ config["final.dir"] +'\' -p \''+ config["pool.key"] +'\' -f \''+ config["farmer.key"] +'\'\"'
    try:
        os.system(commandString)
    except KeyboardInterrupt:
        print("\n\nExecução finalizada!\nAguarde enquanto o programa é finalizado!")
    except Exception as e:
        print("Não conseguiu plotar!")

def finishMadMaxPlotter():
    global plottingStarted

    if(plottingStarted):
        plotEnv('sub')
        removeTempDirs()
        plottingStarted = False
    
    input("Pressione 'Enter' para sair...")
    print(endString)


#Valida se os diretorios estao corretos, caso algum esteja errado finaliza a execucao
for conf in config:
    if "dir" in conf:
        confPath = config[conf]
        if(os.path.exists(confPath)):
            continue
        else:
            print("\nNao foi possivel encontrar o diretorio " + confPath + ", configurado como " + conf + endString)
            tExit()
    else:
        continue

#Funcoes em caso de abortar o programa
atexit.register(finishMadMaxPlotter)

#Inicia a plotagem
startMadMaxPlotter()