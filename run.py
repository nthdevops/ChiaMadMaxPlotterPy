import psutil, os, atexit, shutil, dotenv, subprocess, requests, time, jsonConf, sys
from sys import exit

# Retorna o path do arquivo de acordo com o tipo de execucao, se for binario ou o script diretamente
def filePath():
    path = ""
    if getattr(sys, 'frozen', False):
            path = os.path.dirname(sys.executable)
    else:
        path = os.path.dirname(os.path.abspath(__file__))
    return path

#Declaracao de variaveis globais
endString = "\n\nPrograma finalizado!\nBye Bye :)\n"

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

#API Conf
plotReplaceAPIUrl = "http://"+conf.plotReplaceAPI.host+":"+conf.plotReplaceAPI.port+"/addPlotToDelete"

#Funcao para finalizar o plotter
def finishMadMaxPlotter():
    psPlotCreatingRemoveAll()
    print("\nQuase finalizando..")
    time.sleep(4)
    setEnv(plotCountEnvName, "0")
    removeTempDirs()
    
    print(endString)
    input("Pressione 'Enter' para sair...")

#Funcoes em caso de abortar o programa
atexit.register(finishMadMaxPlotter)

#Valida se os diretorios estao corretos, caso algum esteja errado finaliza a execucao
for dir in conf.finalDirs:
    confPath = dir["path"]
    if(os.path.exists(confPath)):
        continue
    else:
        print("\nNao foi possivel encontrar o diretorio " + confPath + ", configurado como path!" + endString)
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
        exit()

#Funcao de remocao de diretorios
def removeDir(path):
    shutil.rmtree(path, ignore_errors=True)

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
        exit()
    else:
        print("\nPowershell executando!")
    
    return {"psProcess": psProcess, "logName": logName, "created": False}

#Conta o total de plots no diretorio
def getPlotsCount(plotsPath):
    totalPlots = len([f for f in os.listdir(plotsPath) if len(f.split('.plot')) == 2])
    return totalPlots

# A partir de um diretorio do arquivo de configuracao, cria um dict de facil acesso com as informacoes daquele diretorio
def getPlotDirInfos(dir):
    finalPath = dir["path"]
    maxPlots = int(dir["maxPlots"])
    nftAddress = dir["nftAddress"]
    replaceOldPlotsEnabled = dir["replaceOldPlots"]["enabled"]
    replaceOldPlotsDeletePath = dir["replaceOldPlots"]["deletePath"]
    jsonDeletePath = {"deletePath": replaceOldPlotsDeletePath}
    totalPlotsNft = getPlotsCount(finalPath)
    
    dirInfos = {}
    dirInfos["finalPath"] = finalPath
    dirInfos["maxPlots"] = maxPlots
    dirInfos["nftAddress"] = nftAddress
    dirInfos["replaceOldPlotsEnabled"] = replaceOldPlotsEnabled
    dirInfos["replaceOldPlotsDeletePath"] = replaceOldPlotsDeletePath
    dirInfos["jsonDeletePath"] = jsonDeletePath
    dirInfos["totalPlotsNft"] = totalPlotsNft
    return dirInfos

# Printa as informacoes a partir de um dict de dir retornado pela funcao getPlotDirInfos
def printPlotDirInfos(dirInfos):
    print("Conf criacao plot:")
    print("Path final:", dirInfos["finalPath"])
    print("Max Plots:", dirInfos["maxPlots"])
    print("NFT Singleton:", dirInfos["nftAddress"])
    print("Substituir plots antigos:", dirInfos["replaceOldPlotsEnabled"])
    print("Diretorio plots antigos:", dirInfos["replaceOldPlotsDeletePath"])

# Requisita para a API de substituicao de plots a partir das infos de diretorio da funcao getPlotDirInfos
def requestReplaceAPI(dirInfos):
    if(dirInfos["replaceOldPlotsEnabled"]):
        if conf.plotReplaceAPI.ignoreFirst:
            conf.plotReplaceAPI.ignoreFirst = False
            return
        requestSent = False
        while not requestSent:
            try:
                r = requests.post(plotReplaceAPIUrl, json=dirInfos["jsonDeletePath"], timeout=120)
                print("Resposta da reposicao de plots:", r.text, "\nStatusCode:", r.status_code)
            except Exception as e:
                print("\nNao foi possivel requisitar para a API, verifique possiveis problemas. Excecao:\n", e)
            else:
                requestSent = True

# Retorna a valicao de criacao de plot para o diretorio
def canCreatePlot(dirInfos):
    return dirInfos["totalPlotsNft"] < dirInfos["maxPlots"]

# A partir de um elemento da lista psPlotsCreating, inicia a criacao do plot
def plotCreate(psPlotElem):
    psPlotDirInfo = psPlotElem["dirInfo"]
    printPlotDirInfos(psPlotDirInfo)
    psPlotElem["dirInfo"]["totalPlotsNft"] += 1
    requestReplaceAPI(psPlotDirInfo)
    psPlotElem["madMaxProcess"].append(startMadMaxPlotter(1, psPlotDirInfo["finalPath"], psPlotDirInfo["nftAddress"]))

#Valida qual diretorio ira iniciar a nova criacao de plot e inicia
def newPlot():
    #Variavel para dizer se conseguiu ou nao criar plots, indicando que acabou a criacao de plots se o valor for False
    plotCreated = False
    for psPlotElem in psPlotsCreating:
        if canCreatePlot(psPlotElem["dirInfo"]):            
            plotCreate(psPlotElem)
            plotCreated = True
            break
    return plotCreated

# Remove o elemento indicado, da lista de plots em criacao
def psPlotCreatingRemove(psMadMaxProcess, madProcess):
    try:
        madProcess["psProcess"].terminate()
    except:
        pass
    psMadMaxProcess.remove(madProcess)
    plotEnv('sub')

# Remove o elemento indicado, da lista de plots em criacao
def psPlotCreatingRemoveAll():
    try:
        for psPlot in psPlotsCreating:
            for madProcess in psPlot["madMaxProcess"]:
                madProcess["psProcess"].terminate()
                psPlot["madMaxProcess"].remove(madProcess)
                plotEnv('sub')
    except:
        print("Deu ruim")

try:
    # Deleta diretorios temporarios, antes de iniciar a execucao
    removeTempDirs()

    #Cria a fila de criacao de plots
    for dir in conf.finalDirs:
        dirInfo = getPlotDirInfos(dir)
        #Antes de fazer o append para a lista psPlotsCreating, valida se ainda ha espaco para criacao de plots
        if canCreatePlot(dirInfo):
            psPlotsCreating.append({"dirInfo": dirInfo, "madMaxProcess": []})

    #Inicia a criacao do primeiro plot, se nao criar, finaliza o programa, ja que todos os diretorios estao cheios e nao sera necessario criar plots
    if not newPlot():
        exit()

    print(psPlotsCreating)#DELETE
    while(True):
        for idx, psPlot in enumerate(psPlotsCreating):
            if len(psPlot["madMaxProcess"]) > 0:
                dirInfo = psPlot["dirInfo"]
                for madProcess in psPlot["madMaxProcess"]:
                    log = madProcess["logName"]
                    if os.path.isfile(log):
                        for line in open(log, encoding='utf-8-sig').read().splitlines():
                            if not madProcess["created"]:
                                if "Total plot creation time" in line:
                                    print(line,"| log:", log)
                                    madProcess["created"] = True
                                    newPlot()
                                    break
                            elif "Copy to" in line and "finished" in line:
                                print(line,"| log:", log)
                                psPlotCreatingRemove(psPlot["madMaxProcess"], madProcess)
                                print(psPlotsCreating)#DELETE
                                break
            elif not canCreatePlot(psPlot["dirInfo"]):
                psPlotsCreating.remove(psPlot)
                print(psPlotsCreating)#DELETE
        
        #Caso nao exista elementos para criacao de plots, finaliza o loop, partindo para o fim do programa
        if len(psPlotsCreating) == 0:
            break
        time.sleep(5)
except KeyboardInterrupt:
    print("\n\nExecucao finalizada!\nAguarde enquanto o programa eh finalizado!")

# Caso tudo tenha corrido bem, finaliza o programa
exit()