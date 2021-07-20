import psutil, os, atexit, shutil, subprocess, time, jsonConf, sys, signal
from sys import exit
from datetime import datetime
from customLogs import *

# Retorna o path do arquivo de acordo com o tipo de execucao, se for binario ou o script diretamente
def filePath():
    path = ""
    if getattr(sys, 'frozen', False):
            path = os.path.dirname(sys.executable)
    else:
        path = os.path.dirname(os.path.abspath(__file__))
    return path

#Define o diretorio atual do arquivo em execucao
thisFilePath = str(filePath())

#Vai para o diretorio atual do arquivo
os.chdir(thisFilePath)

#Cria o objeto de configuracao do atraves da classe de json
conf = jsonConf.getConf(thisFilePath+'\\conf.json')

#Inicia a configuracao de logs
logger = logger = CustomLog(conf, 'plotter')

#Declaracao de variaveis globais
endString = "Programa finalizado!\nBye Bye :)\n"

#Plotting control
psPlotsCreating = []
plotsLogsHistory = {}

#Funcao para remover os diretorios temporarios
def removeTempDirs():
    try:
        tempDirs = os.listdir(conf.tempDir)
        if len(tempDirs) > 0:
            logger.info("Deletando diretorios temporarios")
            for dir in tempDirs:
                dirDel = conf.tempDir+dir
                logger.info("Deletando diretorio:", dirDel)
                cntTries = 0
                while True:
                    if os.path.exists(dirDel):
                        cntTries += 1
                        removeDir(dirDel)
                    else:
                        logger.info("Diretorio deletado!")
                        break
                    if cntTries >= 20:
                        logger.warning("Nao conseguiu deletar o diretorio!")
                        break
                    time.sleep(1)
    except Exception as e:
        logger.error("Nao conseguiu deletar os diretorios temporarios, Excecao:\n"+ str(e))

#Funcao para finalizar o plotter
def finishMadMaxPlotter():
    logger.info("Finalizando execucao do programa, aguarde!")
    psPlotCreatingRemoveAll()
    logger.info("Quase finalizando..")
    removeTempDirs()
    
    logger.info(endString)
    input("Pressione 'Enter' para sair...")

#Funcoes em caso de abortar o programa
atexit.register(finishMadMaxPlotter)

#Valida se os diretorios estao corretos, caso algum esteja errado finaliza a execucao
for dir in conf.finalDirs:
    confPath = dir["path"]
    if(os.path.exists(confPath)):
        continue
    else:
        logger.error("Nao foi possivel encontrar o diretorio " + confPath + ", configurado como path!")
        exit()

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
        logger.error("Nao foi possivel criar pastas temporarias!\nExcecao:", e)
        exit()

#Funcao de remocao de diretorios
def removeDir(path):
    shutil.rmtree(path, ignore_errors=True)

#Le o log retornando as linhas tratadas
def readLog(logPath):
    if os.path.isfile(logPath):
        with open(logPath, encoding='utf-8-sig') as f:
            lines = f.read().splitlines()
        return lines
    else:
        logger.error("Arquivo de log", logPath, "nao foi encontrado!")
        return [""]

#Valida se existe um texto em uma linha, para inumeros parametros
def checktextInStr(line, *args):
    if args[0] in line:
        if len(args) == 1:
            return True
        foundAll = True
        for arg in args:
            if arg not in line:
                foundAll = False
                break
        if foundAll:
            return True
    return False

#Funcao para iniciar a plotagem
def startMadMaxPlotter(plots, finalDir, contractAdress):
    #Cria o plot name para tempDirs e logs a partir do horario de criacao
    now = datetime.now()
    plotName = "plot_"+now.strftime("%d_%m_%Y__%H-%M-%S")
    logName = conf.logsPath+plotName+".log"
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
        logger.warning("Execucao interrompida!")
    except Exception as e:
        logger.error("Nao conseguiu plotar! Exception:\n",e)
        exit()
    #Retorna um dict com as informacoes de criacao de plot do madMax
    return {"psProcess": psProcess, "logName": logName, "created": False}

#Conta o total de plots no diretorio
def getPlotsCount(plotsPath):
    totalPlots = 0
    if os.path.exists(plotsPath):
        for f in os.listdir(plotsPath):
            if len(f.split('.plot')) == 2:
                if not len(f.split('.tmp')) == 2:
                    totalPlots +=1
    else:
        logger.error("A contagem de plots falhou pois o diretorio", plotsPath, "nao existe!! A execucao sera abortada!")
        exit()
    return totalPlots

#Se existir um arquivo .plot.temp ira deleta-lo
def deleteBrokenTempPlots(plotsPath):
    for f in os.listdir(plotsPath):
        if len(f.split('.plot')) == 2:
            if len(f.split('.tmp')) == 2:
                deletePath = plotsPath+f
                logger.debug("Plot temp detectado, sera deleteado o arquivo:", deletePath)
                os.remove(deletePath)

# A partir de um diretorio do arquivo de configuracao, cria um dict de facil acesso com as informacoes daquele diretorio
def getPlotDirInfos(dir):
    finalPath = dir["path"]
    maxPlots = int(dir["maxPlots"])
    nftAddress = dir["nftAddress"]
    
    dirInfos = {}
    dirInfos["finalPath"] = finalPath
    dirInfos["maxPlots"] = maxPlots
    dirInfos["nftAddress"] = nftAddress
    return dirInfos

#Retorna uma string com as infos do diretorio
def getDirInfosStr(dirInfos):
    returnStr = "Path final: " + str(dirInfos["finalPath"]) + "\nMax Plots: " + str(dirInfos["maxPlots"]) + "\nNFT Singleton: " + str(dirInfos["nftAddress"])
    return returnStr

#Retorna o total de plots no diretorio + os plots em criacao
def getRealTotalPlots(psPlotElem):
    dirInfos = psPlotElem["dirInfo"]
    currentPlotCountInDir = getPlotsCount(dirInfos["finalPath"])
    #O tamanho da lista madMaxProcess, diz quantos plots estão em andamento no momento
    currentPlotsInCreation = len(psPlotElem["madMaxProcess"])
    return currentPlotCountInDir + currentPlotsInCreation

# Retorna a valicao de criacao de plot para o diretorio
def canCreatePlot(psPlotElem):
    dirInfos = psPlotElem["dirInfo"]
    realPlotCount = getRealTotalPlots(psPlotElem)
    maxPlost = dirInfos["maxPlots"]
    #Se os plots em andamento + os plots do diretorio forem menores que o maximo, realmente pode-se criar outro plot
    if realPlotCount < maxPlost:
        return True
    return False

def getPlotCountStr(psPlotElem):
    dirInfos = psPlotElem["dirInfo"]
    realPlotCount = getRealTotalPlots(psPlotElem)
    maxPlost = dirInfos["maxPlots"]
    return ("Contagem de plots do diretorio: " + dirInfos["finalPath"] + ". Quantitade atual: " + str(realPlotCount) + " | Maximo:" + str(maxPlost))

# A partir de um elemento da lista psPlotsCreating, inicia a criacao do plot
def plotCreate(psPlotElem):
    psPlotDirInfo = psPlotElem["dirInfo"]
    #Prints iniciais
    logger.info("=========================================================================================================")
    logger.info("Iniciando criacao de plot!\n")
    logger.info(getDirInfosStr(psPlotDirInfo))
    #Inicia o madMaxPlotter, armazenando o retorno da funcao
    madProcess = startMadMaxPlotter(1, psPlotDirInfo["finalPath"], psPlotDirInfo["nftAddress"])
    #Adiciona a lista de processos do elemento de criacao de plots
    psPlotElem["madMaxProcess"].append(madProcess)
    newLogName = madProcess["logName"]
    logger.info("Iniciou a criacao do plot", getRealTotalPlots(psPlotElem), "de", psPlotElem["dirInfo"]["maxPlots"], "| Arquivo de log:", newLogName)
    cntTries = 0
    #Validacao para o output do madMax, somente dando continuidade quando o arquivo de log for criado, provando que o MadMax iniciou, desiste apos 50 tentativas
    while not os.path.isfile(newLogName):
        cntTries += 1
        if cntTries == 50:
            logger.error("Arquivo de log nao foi encontrado | log:", newLogName)
            break
        time.sleep(0.5)
    newLogLines = None
    cntTries = 0
    mustBreak = False
    #Enquanto nao sair o output com o nome do plot, sai da iteracao para a mensagem de criacao ficar completa, desistindo apos 50 tentativas
    while not mustBreak:
        time.sleep(0.5)
        cntTries += 1
        newLogLines = readLog(newLogName)
        for line in newLogLines:
            if checktextInStr(line, "Plot Name: "):
                logger.info(line)
                mustBreak = True
                break
        if cntTries == 50:
            break
    plotsLogsHistory[madProcess["logName"]] = newLogLines
    logger.info("=========================================================================================================")
    logger.info("Plot em criacao...")
    return True

#Valida qual diretorio ira iniciar a nova criacao de plot e inicia
def newPlot():
    #Variavel para dizer se conseguiu ou nao criar plots, indicando que acabou a criacao de plots se o valor for False no retorno
    plotCreated = False
    for psPlotElem in psPlotsCreating:
        if canCreatePlot(psPlotElem):
            plotCreate(psPlotElem)
            plotCreated = True
            break
    return plotCreated

# Remove da lista de plots em criacao, o elemento indicado
def psPlotCreatingRemove(psMadMaxProcess, madProcess):
    try:
        madProcess["psProcess"].terminate()
    except:
        pass
    plotsLogsHistory.pop(madProcess["logName"], None)
    psMadMaxProcess.remove(madProcess)

# Remove todos os elementos da lista de plots em criacao
def psPlotCreatingRemoveAll():
    for psPlot in psPlotsCreating:
        for madProcess in psPlot["madMaxProcess"]:
            psPlotCreatingRemove(psPlot["madMaxProcess"], madProcess)

try:
    # Deleta diretorios temporarios, antes de iniciar a execucao
    removeTempDirs()

    #Cria a fila de criacao de plots
    for dir in conf.finalDirs:
        dirInfo = getPlotDirInfos(dir)
        if conf.deleteTempBeforeStart:
            deleteBrokenTempPlots(dir["path"])
        #Antes de fazer o append para a lista psPlotsCreating, valida se ainda ha espaco para criacao de plots
        if getPlotsCount(dir["path"]) < dir["maxPlots"]:
            psElem = {"dirInfo": dirInfo, "madMaxProcess": []}
            psPlotsCreating.append(psElem)
            logger.debug("Elemento adicionado para criacao:")
            logger.debug(getDirInfosStr(dirInfo))
            logger.debug(getPlotCountStr(psElem))
        else:
            logger.info("=========================================================================================================")
            logger.info("Nao sera necessaria a criacao de plots para o dir:")
            logger.info(getDirInfosStr(dirInfo))
            logger.info("O numero maximo de plots ja foi atingido!")
            logger.info("=========================================================================================================")

    #Inicia a criacao do primeiro plot, se nao criar, finaliza o programa, ja que todos os diretorios estao cheios e nao sera necessario criar plots
    if not newPlot():
        exit()

    while(True):
        #Itera sobre a lista de criacao de plots
        for psPlot in psPlotsCreating:
            #Valida se para o elemento da lista, existem plots em criacao atraves da lista que controla processo do madMax
            if len(psPlot["madMaxProcess"]) > 0:
                #Itera sobre todos os processos em andamento na lista
                for madProcess in psPlot["madMaxProcess"]:
                    log = madProcess["logName"]
                    logLines = readLog(log)
                    if logLines != None:
                        #So entra nas validacoes se o log foi alterado, caso esteja igual ao historico, nao realiza nenhuma acao
                        if logLines != plotsLogsHistory[log]:
                            for line in logLines:
                                #Somente valida linhas novas do arquivo de log, evitando reprocessamento desnecessario
                                if line not in plotsLogsHistory[log]:
                                    #Print caso o log seja sobre a finalizacao de uma das fases do MadMax
                                    if checktextInStr(line, "Phase ", " took "):
                                        logger.info(line)
                                    #Valida atraves do atributo de criacao de log se o log ainda esta sendo criado
                                    elif not madProcess["created"]:
                                        #Checka atraves da mensagem se o log foi criado, caso sim, print da finalizacao, deleta um plot antigo e inicia outra criacao de plot
                                        if checktextInStr(line, "Started copy to "):
                                            logger.info(line,"| log:", log)
                                            madProcess["created"] = True
                                            newPlot()
                                            continue
                                        else:
                                            logger.debug("MadMax:", line)
                                    #Caso seja um plot ja criado, valida se a copia do arquivo foi terminada, caso sim, elimina o elemento da lista de processos do madMax
                                    elif checktextInStr(line, "Copy to", "finished, took"):
                                        logger.info(line, "| log:", log)
                                        psPlotCreatingRemove(psPlot["madMaxProcess"], madProcess)
                                        break
                                    else:
                                        logger.debug("MadMax:", line)
                            #Adiciona as novas linhas de log ao historico, apos o processamento finalizar
                            plotsLogsHistory[log] = logLines
            #Se o primeiro if, disser que a lista de processos do madMax esta vazia, ira validar para que remova da lista de criacao de plots caso nao seja possivel criar novos plots para o diretorio em questao
            elif not canCreatePlot(psPlot):
                logger.info("=========================================================================================================")
                logger.info("Criacao de plots finalizada para:")
                logger.info(getDirInfosStr(psPlot["dirInfo"]))
                psPlotsCreating.remove(psPlot)
                logger.info("=========================================================================================================")
        
        #Caso nao exista elementos para criacao de plots, finaliza o loop, partindo para o fim do programa
        if len(psPlotsCreating) == 0:
            logger.info("---------------------------------------------------------------------------------------------------------")
            logger.info("Criacao de plots finalizada para todos os diretorios!\n\nO programa ira finalizar em breve!")
            logger.info("---------------------------------------------------------------------------------------------------------")
            break
        time.sleep(5)
except KeyboardInterrupt:
    logger.warning("Execucao interrompida!")

# Caso tudo tenha corrido bem, finaliza o programa
exit()