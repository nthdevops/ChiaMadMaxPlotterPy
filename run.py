import psutil, os, atexit, shutil, dotenv, subprocess, requests, time, jsonConf, sys

#Declaracao de variaveis globais
endString = "\n\nPrograma finalizado!\nBye Bye :)\n"
def filePath():
    path = ""
    if getattr(sys, 'frozen', False):
            path = os.path.dirname(sys.executable)
    else:
        if __file__:
            path = os.path.dirname(__file__)
    return path
thisFilePath = str(filePath())
#Vai para o diretorio atual do arquivo
os.chdir(thisFilePath)

#Plotting control vars and envs
plotCountEnvName = "nOfPlots"
if not os.path.exists(thisFilePath+"\\.env"):
    open(thisFilePath+"\\.env", 'w').close()
envConf = dotenv.dotenv_values(".env")
psPlotsCreating = []

#Cria o objeto de configuracao do atraves da classe de json
conf = jsonConf.getConf(thisFilePath+'\\conf.json')

#API Conf
plotReplaceAPIUrl = "http://"+conf.plotReplaceAPI.host+":"+conf.plotReplaceAPI.port+"/addPlotToDelete"

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
        tempDirs = os.listdir(conf.tempDir)
        if len(tempDirs) > 0:
            print("\nDeletando diretorios temporarios")
            for dir in tempDirs:
                dirDel = conf.tempDir+dir
                print("Deletando diretorio:", dirDel)
                removeDir(dirDel)
        else:
            print("Nao foi necessario deletar diretorios")
    except Exception as e:
        print("\nNao conseguiu deletar os diretorios temporarios, Excecao:\n"+ str(e) + endString)

#Funcao para iniciar a plotagem
def startMadMaxPlotter(plots, finalDir, contractAdress):
    #Acessa dentro da funcao as variaveis globais

    #Define o plot na env var para mais um e cria os diretorios temporarios
    plotEnv('sum')
    plotNumber = getEnv(plotCountEnvName)
    plotName = "plot"+plotNumber
    logName = conf.logsPath + plotName+".log"
    tempDir1 = conf.tempDir+plotName+"Temp1\\"
    tempDir2 = conf.tempDir+plotName+"Temp2\\"
    createTempDir(tempDir1)
    createTempDir(tempDir2)
    #Define a quantidade de threads a serem utilizadas
    totalThreads = int(conf.threads)
    if(totalThreads < 0):
        totalThreads = psutil.cpu_count()

    commandString = 'powershell \".\chia_plot.exe -n \'' + str(plots) +'\' -r \'' + str(totalThreads) + '\' -t \'' + tempDir1 + '\' -2 \'' + tempDir2 + '\' -d \'' + str(finalDir) + '\' -c \'' + str(contractAdress) + '\' -f \'' + conf.farmerKey + '\' | Out-File \'' + logName + '\' -Encoding UTF8\"'

    psProcess = None
    try:
        psProcess = subprocess.Popen(commandString)
    except KeyboardInterrupt:
        print("\n\nExecucao finalizada!\nAguarde enquanto o programa eh finalizado!")
    except Exception as e:
        print("\nNao conseguiu plotar!\n",e)
    else:
        print("\nPowershell executando!")
    
    return {"psProcess": psProcess, "logName": logName, "created": False}

def psPlotCreatingRemove(psPlotElem):
    try:
        psPlotElem["psProcess"].terminate()
    except:
        print("Nao foi necessario finalizar o processo")
    psPlotsCreating.remove(psPlotElem)
    plotEnv('sub')

def finishMadMaxPlotter():
    for psPlot in psPlotsCreating:
        psPlotCreatingRemove(psPlot)
    time.sleep(3)
    setEnv(plotCountEnvName, "0")
    removeTempDirs()
    
    input("Pressione 'Enter' para sair...")
    print(endString)

def getPlotsCount(plotsPath):
    totalPlots = len([f for f in os.listdir(plotsPath) if len(f.split('.plot')) == 2])
    return totalPlots

def requestReplaceAPI(replaceOldPlotsEnabled):
    if(replaceOldPlotsEnabled):
        if conf.plotReplaceAPI.ignoreFirst:
            conf.plotReplaceAPI.ignoreFirst = False
            return
        requestSent = False
        while not requestSent:
            try:
                r = requests.post(plotReplaceAPIUrl, json=jsonDeletePath, timeout=120)
            except Exception as e:
                print("Nao foi possivel requisitar para a API, verifique possiveis problemas. Excecao:\n", e)
            else:
                requestSent = True

#Valida se os diretorios estao corretos, caso algum esteja errado finaliza a execucao
for dir in conf.finalDirs:
    confPath = dir["path"]
    if(os.path.exists(confPath)):
        continue
    else:
        print("\nNao foi possivel encontrar o diretorio " + confPath + ", configurado como path!" + endString)
        tExit()

#Funcoes em caso de abortar o programa
atexit.register(finishMadMaxPlotter)

try:
    #Controle de plotagem
    for dir in conf.finalDirs:
        finalPath = dir["path"]
        maxPlots = int(dir["maxPlots"])
        nftAddress = dir["nftAddress"]
        replaceOldPlotsEnabled = dir["replaceOldPlots"]["enabled"]
        replaceOldPlotsDeletePath = dir["replaceOldPlots"]["deletePath"]
        print("Conf criacao plot:")
        print("Path final:", finalPath)
        print("Max Plots:", maxPlots)
        print("NFT Singleton:", nftAddress)
        print("Substituir plots antigos:", replaceOldPlotsEnabled)
        print("Diretorio plots antigos:", replaceOldPlotsDeletePath)
        totalPlotsNft = getPlotsCount(finalPath)
        jsonDeletePath = {"deletePath": replaceOldPlotsDeletePath}

        def plotCreate():
            requestReplaceAPI(replaceOldPlotsEnabled)
            psPlotsCreating.append(startMadMaxPlotter(1, finalPath, nftAddress))

        while(True):
            if totalPlotsNft < maxPlots:
                if(len(psPlotsCreating) == 0):
                    plotCreate()

                for psPlot in psPlotsCreating:
                    if not psPlot["created"]:
                        log = psPlot["logName"]
                        if os.path.isfile(log):
                            for line in open(log, encoding='utf-8-sig').read().splitlines():
                                if "Total plot creation time" in line:
                                    print("Criacao de plot finalizada, ira iniciar outro plot, log:", log)
                                    psPlot["created"] = True
                                    totalPlotsNft += 1
                                    if totalPlotsNft < maxPlots:
                                        plotCreate()
                                    continue
            else:
                for psPlot in psPlotsCreating:
                    log = psPlot["logName"]
                    if os.path.isfile(log):
                        for line in open(log, encoding='utf-8-sig').read().splitlines():
                            if "Copy to" in line and "finished" in line:
                                print("Copia finalizada, ira remover da lista de plots em criacao, log:", log)
                                psPlotCreatingRemove(psPlot)
                                continue
                if len(psPlotsCreating) == 0:
                    print("Finalizou a criacao de todos os plots para o diretorio final", dir)
                    break
            time.sleep(5)
except KeyboardInterrupt:
    print("\n\nExecucao finalizada!\nAguarde enquanto o programa eh finalizado!")