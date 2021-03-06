import ROOT as R

import numpy as np
from copy import deepcopy
import sys

import smoothfit
import BackgroundFit_MultiChannel as BkgFit

import SystematicsTools as SystTools
import SystematicsTools_withSmoothing as SystToolsSmooth
import ExpModGaussSmoothingSystematics as EMGSmoothSyst

from HistoTools import HistLocationString as HistLocStr
from HistoTools import CheckAndGet
# from HistoTools import BlindData2bSR ---> no longer needed, since they are blinded during histogram production


func1 = None
func2 = None

# rebinFinal -- added by Qi. should be array object. Do the rebinning before writing into output files
# nbtag_top_shape_normFit --- what top shape to be used in NORMALIZATION FIT?
# nbtag_top_shape_SRPred --- what top shape to be used in SR prediction?
def HistoAnalysis(datafileName="data/hist_data.root",
                  topfileName="data/hist_ttbar.root",
                  zjetfileName=None,
                  distributionName= "mHH_pole",
                  n_trkjet  = ["4","3","2"],
                  n_btag    = ["4","3","2"],
                  btag_WP     = "77",
                  NRebin = 10,
                  use_one_top_nuis = False,
                  use_scale_top_0b = False,
                  nbtag_top_shape_normFit_for4b = "33",
                  nbtag_top_shape_SRPred_for4b = "33",
                  rebinFinal = None,
                  smoothing_func = "Dijet",
                  top_smoothing_func = "Dijet",
                  inputFitResult = None,
                  inputQCDSyst_Dict = None,
                  doSmoothing = True,
                  addSmoothErrorBin = False,
                  qcdSmoothRange = (1200, 3000),# (100, 2500),
                  topSmoothRange = (1200, 3000), #(100, 2000),
                  isSystematicVariation = False,
                  verbose = False,
                  makeOutputFiles = True,
                  MassRegionName = "SR"
                  ):

    global func1
    global func2
    
    ##### Parse Inputs ############################################
    dist_name   = distributionName
    
    num_trkjet  = np.asarray(n_trkjet)
    if num_trkjet.shape==():
        num_trkjet = np.asarray([n_trkjet])

    num_btag    = np.asarray(n_btag)
    if num_btag.shape==():
        num_btag = np.asarray([n_btag])
    if num_btag.shape!=num_trkjet.shape:
        print "Must have same number of track jet and b-tag regions specified"
        sys.exit(0)
  
    btag_WP     = btag_WP
    
    n_rebin     = NRebin

    nbtag_top_shape_for4b = nbtag_top_shape_SRPred_for4b
    topShape_nbtag_for4b = nbtag_top_shape_for4b
    if nbtag_top_shape_for4b == None:
        topShape_nbtag_for4b = num_btag+num_btag

    useOneTopNuis = use_one_top_nuis

    scaleTop0b = use_scale_top_0b

    n_channels = num_trkjet.shape[0]

    regions = [ num_trkjet[i]+num_btag[i] for i in range(n_channels) ]


    ##for outputing
    isMhhDistribution = (distributionName=="mHH_l" or distributionName=="mHH_pole")

    do_smoothing  = (doSmoothing if isMhhDistribution else False)   # qi

    ##################################################################



    
    ##### Storage Variables ############################################
    output_Dict = { }

    
    Nbkg_dict    = {  }
    Nbkg_SysList = {  }
    for ir in regions:
        Nbkg_dict[ir]    = { "qcd":0,  "top":0,  "zjet":0,  "bkg":0 }
        Nbkg_SysList[ir] = { "qcd":[], "top":[], "zjet":[], "bkg":[] }


    vartxt = ''
    ##################################################################


    
    ##### Do Background Fits ############################################
    if inputFitResult == None:
        bkgFitResults = BkgFit. BackgroundFit(datafileName=datafileName,
                                              topfileName=topfileName,
                                              zjetfileName=zjetfileName,
                                              distributionName= "leadHCand_Mass",
                                              n_trkjet  = n_trkjet,
                                              n_btag    = n_btag,
                                              btag_WP     = btag_WP,
                                              NRebin = 2,#NRebin,
                                              use_one_top_nuis = use_one_top_nuis,
                                              use_scale_top_0b = use_scale_top_0b,
                                              nbtag_top_shape_for4b = nbtag_top_shape_normFit_for4b,
                                              makePlots = True,
                                              verbose = verbose )

    else:
        bkgFitResults = inputFitResult

    pvars = bkgFitResults["pvars"]

    output_Dict["fitResults"] = bkgFitResults
    ##################################################################


    ##### Get QCD Shape Systematics from CR  ##############################
    if MassRegionName == "SR":
        # should only affect SR
        if inputQCDSyst_Dict == None and isMhhDistribution:  # qi
            QCDSyst_Dict =  SystToolsSmooth.QCDSystematics(datafileName=datafileName,
                                        topfileName=topfileName,
                                        zjetfileName=zjetfileName,
                                        distributionName= "mHH_l",   # this has been decided to fix on DiJetMass
                                        n_trkjet  = n_trkjet,
                                        n_btag    = n_btag,
                                        btag_WP     = btag_WP,
                                        mu_qcd_vals = bkgFitResults["muqcd"],
                                        topscale_vals = bkgFitResults["topscale"],
                                        NRebin = 5,
                                        smoothing_func = smoothing_func,
                                        SmoothRange = (1100, 3000),# (100, 2500),
                                        use_one_top_nuis = use_one_top_nuis,
                                        use_scale_top_0b = use_scale_top_0b,
                                        nbtag_top_shape_for4b = nbtag_top_shape_SRPred_for4b,
                                        makePlots = True,
                                        verbose = False,
                                        outfileNameBase="QCDSysfitSmooth.root")

            
            ## QCDSyst_Dict = SystTools.QCDSystematics(datafileName=datafileName,
            ##                                         topfileName=topfileName,
            ##                                         zjetfileName=zjetfileName,
            ##                                         distributionName= "mHH_l",   # this has been decided to fix on DiJetMass
            ##                                         n_trkjet  = n_trkjet,
            ##                                         n_btag    = n_btag,
            ##                                         btag_WP     = btag_WP,
            ##                                         mu_qcd_vals = bkgFitResults["muqcd"],
            ##                                         topscale_vals = bkgFitResults["topscale"],
            ##                                         NRebin = NRebin,
            ##                                         use_one_top_nuis = use_one_top_nuis,
            ##                                         use_scale_top_0b = use_scale_top_0b,
            ##                                         nbtag_top_shape_for4b = nbtag_top_shape_SRPred_for4b,
            ##                                         makePlots = True,
            ##                                         verbose = False,
            ##                                         outfileNameBase="QCDSysfit.root")
            
        elif inputQCDSyst_Dict != None:
            QCDSyst_Dict = inputQCDSyst_Dict

        else:
            QCDSyst_Dict = None
    else:
        QCDSyst_Dict = None

    output_Dict["QCDSystCR"] = QCDSyst_Dict
    ##################################################################


    

    ##### Get Signal Region Histograms ################################
    datafile = R.TFile(datafileName,"READ")
    topfile  = R.TFile(topfileName,"READ")
    zjetfile  = ( R.TFile(zjetfileName,"READ") if zjetfileName!=None else None)


    histos = {}
    
    # collect all histograms
    for r in ["44","33","22","40","30","20"]:
        # folder_r = HistLocStr(dist_name, r[0], r[1], btag_WP, "SR")  #folder( r[0], r[1], btag_WP)
        folder_r = HistLocStr(dist_name, r[0], r[1], btag_WP, MassRegionName)  #folder( r[0], r[1], btag_WP)
        
        data_r   = datafile.Get(folder_r).Clone("data_"+r)
        data_r.SetDirectory(0)
        # if (r == "42") and (MassRegionName == "SR") and blindData2bSR and ( (distributionName == "DiJetMass") or (distributionName == "DiJetMassPrime") ):
        #     data_r = BlindData2bSR(data_r)
        
        top_r    = topfile.Get(folder_r).Clone("top_"+r)
        top_r.SetDirectory(0)

        zjet_r   = CheckAndGet(zjetfile, folder_r, top_r).Clone("zjet_"+r)
        zjet_r.SetDirectory(0)

        for ibin in range(1, top_r.GetNbinsX()+1):
            if top_r.GetBinContent(ibin) < 0:
                top_r.SetBinContent(ibin, 0)
                top_r.SetBinError(ibin, 0)


        data_r.Rebin(n_rebin)
        top_r.Rebin(n_rebin)
        zjet_r.Rebin(n_rebin)

                

        histos[r]     = {"data": data_r,  "top": top_r,  "zjet":zjet_r}

    datafile.Close()
    topfile.Close()
    if zjetfile != None:
        zjetfile.Close()
    ##################################################################



    
    ##### scaling and subtractions #################################
    for ir in range(len(regions)):
        r = regions[ir]

        output_Dict[r] = {"qcd":{}, "ttbar":{}, "zjet":{}}
        
        if makeOutputFiles:
            outfileStat = R.TFile("outfile_boosted_"+r+".root","RECREATE")
        
        r_0b = r[0]+"0"
        #r_3b = r[0]+"3"

        top_0b = histos[r_0b]["top"].Clone("top_0b__"+r)
        if scaleTop0b:
            top_0b.Scale( (bkgFitResults["topscale"][0] if use_one_top_nuis else bkgFitResults["topscale"][ir]) )

        zjet_0b = histos[r_0b]["zjet"].Clone("zjet_0b__"+r)

        qcd_r = histos[r_0b]["data"].Clone("qcd__"+r)
        qcd_r.Add( top_0b, -1)      # added by Qi --- we still want top to be subtracted, given that their fraction is increasing in Run 2.
        qcd_r.Add( zjet_0b, -1)
        qcd_int = qcd_r.Integral()


        for ibin in range(1, qcd_r.GetNbinsX()+1):
            if qcd_r.GetBinContent(ibin) < 0:
                qcd_r.SetBinContent(ibin, 0)
                qcd_r.SetBinError(ibin, 0)


        top_r = histos[r]["top"].Clone("top__"+r)
        if (nbtag_top_shape_for4b =="33") and (r == "44") and (MassRegionName == "SR"):   # the 3b top shape is only used during the SR prediction for 44 region
            temp_scaler = top_r.Integral() / histos[nbtag_top_shape_for4b]["top"].Integral()
            top_r = histos[nbtag_top_shape_for4b]["top"].Clone("top__"+r)
            top_r.Scale( temp_scaler )
        top_int = top_r.Integral()

        zjet_r = histos[r]["zjet"].Clone("zjet__"+r)


        mu_qcd = bkgFitResults["muqcd"][ir]
        top_scale = (bkgFitResults["topscale"][0] if use_one_top_nuis else bkgFitResults["topscale"][ir])
        
        qcd_r.Scale( mu_qcd )
        top_r.Scale( top_scale )

        # store some numbers for table later
        e_qcd = R.Double(0.0)
        e_top = R.Double(0.0)
        Nbkg_dict[r]["qcd"] = qcd_r.IntegralAndError(0, qcd_r.GetNbinsX()+1, e_qcd)
        Nbkg_dict[r]["top"] = top_r.IntegralAndError(0, top_r.GetNbinsX()+1, e_top)
        Nbkg_dict[r]["bkg"] = Nbkg_dict[r]["qcd"] + Nbkg_dict[r]["top"]


        Nbkg_SysList[r]["qcd"].append( float(e_qcd) )
        Nbkg_SysList[r]["top"].append( float(e_top) )
        Nbkg_SysList[r]["bkg"].append( np.sqrt(float(e_qcd)**2 + float(e_top)**2) )   # Qi Question
        
        

        ## Now do smoothing ###########################################################################################
        if do_smoothing:
            ## qcd_normed = qcd_r.Clone("normed")
            ## qcd_normed.SetDirectory(0)
            ## qcd_normed.Scale(1.0 / qcd_normed.Integral())
            ## qcd_normed_sm = smoothfit.smoothfit(qcd_normed, fitFunction = smoothing_func, fitRange = qcdSmoothRange, makePlots = True, verbose = True, outfileName="qcd_normed_smoothfit_"+r+".root")
            
            qcd_sm = smoothfit.smoothfit(qcd_r, fitFunction = smoothing_func, fitRange = qcdSmoothRange, makePlots = True, verbose = False, outfileName="qcd_smoothfit_"+r+".root")
            top_sm = smoothfit.smoothfit(top_r, fitFunction = top_smoothing_func, fitRange = topSmoothRange, makePlots = True, verbose = False, outfileName="top_smoothfit_"+r+".root")
    
            if addSmoothErrorBin:
                qcd_final = smoothfit.MakeSmoothHistoWithError(qcd_r, qcd_sm)
                top_final = smoothfit.MakeSmoothHistoWithError(top_r, top_sm)
            else:
                qcd_final = smoothfit.MakeSmoothHisto(qcd_r, qcd_sm["nom"])
                top_final = smoothfit.MakeSmoothHisto(top_r, top_sm["nom"])

            qcd_final.SetNameTitle("qcd_hh_"+r+"__clone",   "qcd_hh_"+r+"__clone")
            top_final.SetNameTitle("ttbar_hh_"+r+"__clone", "ttbar_hh_"+r+"__clone")
            
        else:
            qcd_final = qcd_r.Clone("qcd_hh_"+r+"__clone")
            top_final = top_r.Clone("ttbar_hh_"+r+"__clone")

        zjet_final = zjet_r.Clone("zjet_hh_"+r+"__clone")


        if rebinFinal is not None:
            qcd_final = qcd_final.Rebin(len(rebinFinal)-1, qcd_final.GetName()+"_rebinFinal", rebinFinal)
            top_final = top_final.Rebin(len(rebinFinal)-1, top_final.GetName()+"_rebinFinal", rebinFinal)
            zjet_final = zjet_final.Rebin(len(rebinFinal)-1, zjet_final.GetName()+"_rebinFinal", rebinFinal)


        if makeOutputFiles:
            outfileStat.WriteTObject(qcd_final, "qcd_hh","Overwrite")
            outfileStat.WriteTObject(top_final, "ttbar_hh","Overwrite")
            outfileStat.WriteTObject(zjet_final, "zjet_hh","Overwrite")


        qcd_final.SetDirectory(0)
        top_final.SetDirectory(0)
        zjet_final.SetDirectory(0)
        output_Dict[r]["qcd"]["nom"] = qcd_final
        output_Dict[r]["ttbar"]["nom"] = top_final
        output_Dict[r]["zjet"]["nom"] = zjet_final

        # for systematics, don't need anything after this in loop
        if isSystematicVariation:
            continue

        ##################################################################################################################################
        ### propagate correlated systematics from the smoothing procedure---> these "replace" the stat error on the bins     #############
        ##################################################################################################################################
        if do_smoothing:
            
            ## qcd smoothing variations#################################################################
            if not addSmoothErrorBin:
                for ivar in range(len(qcd_sm["vars"])):
                    qup = qcd_sm["vars"][ivar][0]
                    qdw = qcd_sm["vars"][ivar][1]

                    qcd_r_qup = smoothfit.MakeSmoothHisto(qcd_r, qup)
                    qcd_r_qdw = smoothfit.MakeSmoothHisto(qcd_r, qdw)

                    qcd_r_qup.SetNameTitle("qcd_hh_"+r+"_smoothQ"+str(ivar)+"Up__clone", "qcd_hh_"+r+"_smoothQ"+str(ivar)+"Up__clone")
                    qcd_r_qdw.SetNameTitle("qcd_hh_"+r+"_smoothQ"+str(ivar)+"Down__clone", "qcd_hh_"+r+"_smoothQ"+str(ivar)+"Down__clone")


                    if rebinFinal is not None:
                        qcd_r_qup = qcd_r_qup.Rebin(len(rebinFinal)-1, qcd_r_qup.GetName()+"_rebinFinal", rebinFinal)
                        qcd_r_qdw = qcd_r_qdw.Rebin(len(rebinFinal)-1, qcd_r_qdw.GetName()+"_rebinFinal", rebinFinal)

                    if makeOutputFiles:
                        outfileStat.WriteTObject(qcd_r_qup, "qcd_hh_smoothQ"+str(ivar)+"Up","Overwrite")
                        outfileStat.WriteTObject(qcd_r_qdw, "qcd_hh_smoothQ"+str(ivar)+"Down","Overwrite")

                    qcd_r_qup.SetDirectory(0)
                    qcd_r_qdw.SetDirectory(0)
                    output_Dict[r]["qcd"]["smoothQ"+str(ivar)+"Up"] = qcd_r_qup
                    output_Dict[r]["qcd"]["smoothQ"+str(ivar)+"Down"] = qcd_r_qdw


                
            ## qcd smoothing function variations #################################################################
            if smoothing_func == "ExpModGauss":
                smoothFuncCompSyst = EMGSmoothSyst.smoothFuncCompare(qcd_r, fitFunction = smoothing_func,
                                                                     fitRange = qcdSmoothRange, funcCompareRange=(900, qcdSmoothRange[1]),
                                                                     makePlots = True, verbose = False, outfileName="EMGSmoothFuncCompare_"+r+".root", plotExtra=False)  # Qi
            else:
                # smoothFuncCompSyst = smoothfit.smoothFuncCompare(qcd_r, fitRange = (900, qcdSmoothRange[1]),
                smoothFuncCompSyst = smoothfit.smoothFuncCompare(qcd_r, fitRange = (qcdSmoothRange[0], qcdSmoothRange[1]),            # qi
                                                                 makePlots = True, verbose = False, outfileName="smoothFuncCompare_"+r+".root", plotExtra=False)  # Qi
                
            qcd_r_func_up = smoothFuncCompSyst["up"]
            qcd_r_func_dw = smoothFuncCompSyst["dw"]
            qcd_r_func_up_super = smoothFuncCompSyst["up_super"]
            qcd_r_func_dw_super = smoothFuncCompSyst["dw_super"]

            if rebinFinal is not None:
                qcd_r_func_up = qcd_r_func_up.Rebin(len(rebinFinal)-1, qcd_r_func_up.GetName()+"_rebinFinal", rebinFinal)
                qcd_r_func_dw = qcd_r_func_dw.Rebin(len(rebinFinal)-1, qcd_r_func_dw.GetName()+"_rebinFinal", rebinFinal)

            if makeOutputFiles:
                outfileStat.WriteTObject(qcd_r_func_up, "qcd_hh_smoothFuncUp","Overwrite")
                outfileStat.WriteTObject(qcd_r_func_dw, "qcd_hh_smoothFuncDown","Overwrite")
                
                outfileStat.WriteTObject(qcd_r_func_up_super, "qcd_hh_smoothFuncSuperUp","Overwrite")
                outfileStat.WriteTObject(qcd_r_func_dw_super, "qcd_hh_smoothFuncSuperDown","Overwrite")

            # treat negative bin
            for ibin in range(1, qcd_r_func_up.GetNbinsX()+1):
                if qcd_r_func_up.GetBinContent(ibin) < 0:
                    qcd_r_func_up.SetBinContent(ibin, 0)
                    qcd_r_func_up.SetBinError(ibin, 0)

                if qcd_r_func_dw.GetBinContent(ibin) < 0:
                    qcd_r_func_dw.SetBinContent(ibin, 0)
                    qcd_r_func_dw.SetBinError(ibin, 0)

                if qcd_r_func_up_super.GetBinContent(ibin) < 0:
                    qcd_r_func_up_super.SetBinContent(ibin, 0)
                    qcd_r_func_up_super.SetBinError(ibin, 0)

                if qcd_r_func_dw_super.GetBinContent(ibin) < 0:
                    qcd_r_func_dw_super.SetBinContent(ibin, 0)
                    qcd_r_func_dw_super.SetBinError(ibin, 0)


            qcd_r_func_up.SetDirectory(0)
            qcd_r_func_dw.SetDirectory(0)
            output_Dict[r]["qcd"]["smoothFuncUp"] = qcd_r_func_up
            output_Dict[r]["qcd"]["smoothFuncDown"] = qcd_r_func_dw

            qcd_r_func_up_super.SetDirectory(0)
            qcd_r_func_dw_super.SetDirectory(0)
            output_Dict[r]["qcd"]["smoothFuncUp_super"] = qcd_r_func_up_super
            output_Dict[r]["qcd"]["smoothFuncDown_super"] = qcd_r_func_dw_super
            
            #smoothfit.smoothFuncRangeCompare(qcd_r, fitRange = (900, qcdSmoothRange[1]), makePlots = True, verbose = False, outfileName="smoothFuncRangeCompare_"+r+".root")
            
            smoothfit.smoothFuncRangeCompare(qcd_r, fitFunction = smoothing_func, fitRange = qcdSmoothRange, fitMaxVals = ["1750", "2000","2500"], fitMinVals=[str(qcdSmoothRange[0]),"1200","1500"],
                                            makePlots = True, plotExtra = False, verbose = False, outfileName="smoothFuncRangeCompare_"+r+".root")   # Qi
            
            ## ttbar smoothing variations##############################################################################
            if not addSmoothErrorBin:
                for ivar in range(len(top_sm["vars"])):
                    tup = top_sm["vars"][ivar][0]
                    tdw = top_sm["vars"][ivar][1]

                    top_r_tup = smoothfit.MakeSmoothHisto(top_r, tup)
                    top_r_tdw = smoothfit.MakeSmoothHisto(top_r, tdw)

                    top_r_tup.SetNameTitle("ttbar_hh_"+r+"_smoothT"+str(ivar)+"Up__clone",   "ttbar_hh_"+r+"_smoothT"+str(ivar)+"Up__clone")
                    top_r_tdw.SetNameTitle("ttbar_hh_"+r+"_smoothT"+str(ivar)+"Down__clone", "ttbar_hh_"+r+"_smoothT"+str(ivar)+"Down__clone")

                    if rebinFinal is not None:
                        top_r_tup = top_r_tup.Rebin(len(rebinFinal)-1, top_r_tup.GetName()+"_rebinFinal", rebinFinal)
                        top_r_tdw = top_r_tdw.Rebin(len(rebinFinal)-1, top_r_tdw.GetName()+"_rebinFinal", rebinFinal)

                    if makeOutputFiles:
                        outfileStat.WriteTObject(top_r_tup, "ttbar_hh_smoothT"+str(ivar)+"Up","Overwrite")
                        outfileStat.WriteTObject(top_r_tdw, "ttbar_hh_smoothT"+str(ivar)+"Down","Overwrite")

                    top_r_tup.SetDirectory(0)
                    top_r_tdw.SetDirectory(0)
                    output_Dict[r]["ttbar"]["smoothT"+str(ivar)+"Up"] = top_r_tup
                    output_Dict[r]["ttbar"]["smoothT"+str(ivar)+"Down"] = top_r_tdw

            

        ########################################################################################################
        ### propagate correlated systematics from normalization fits for mu_qcd and top_scale    ###############
        ########################################################################################################
        for ivar in range(len(pvars)):
            sys_qcd = []
            sys_top = []
            sys_bkg = []
            for iUD in range(2):
                UpDw = ("Up" if iUD ==0 else "Down")
                
                mu_qcd_var = pvars[ivar][iUD][ir]
                top_scale_var = pvars[ivar][iUD][n_channels + (0 if use_one_top_nuis else ir) ]

                qvar = qcd_r.Clone("qvar")
                qvar.Scale( mu_qcd_var * qcd_int / qvar.Integral() )

                ## for ibin in range(1, qvar.GetNbinsX()+1):
                ##     if qvar.GetBinError(ibin) > qvar.GetBinContent(ibin):
                ##         qvar.SetBinError(ibin, qvar.GetBinContent(ibin))
                
                tvar = top_r.Clone("tvar")
                tvar.Scale( top_scale_var * top_int / tvar.Integral() )

                ### store some numbers for table
                sys_qcd.append( qvar.Integral() - Nbkg_dict[r]["qcd"] )
                sys_top.append( tvar.Integral() - Nbkg_dict[r]["top"] )
                sys_bkg.append( qvar.Integral() + tvar.Integral() - Nbkg_dict[r]["bkg"] )

                #vartxt = vartxt + str(r) + ' ' + str(ivar) + ' ' + str(iUD) + ' ' + str(qvar.Integral()) + ' ' + str(tvar.Integral()) + ' ' + str( (qvar.Integral() + tvar.Integral())) + '\n'

                ## Now do smoothing #######
                if do_smoothing:
                    qvar_sm = smoothfit.smoothfit(qvar, fitFunction = smoothing_func, fitRange = qcdSmoothRange, makePlots = False, verbose = verbose,
                                                  outfileName="qcd_smoothfit_"+r+"_Norm"+str(ivar)+str(iUD)+".root")
                    tvar_sm = smoothfit.smoothfit(tvar, fitFunction = top_smoothing_func, fitRange = topSmoothRange, makePlots = False, verbose = verbose,
                                                  outfileName="top_smoothfit_"+r+"_Norm"+str(ivar)+str(iUD)+".root")

                    if addSmoothErrorBin:
                        qvar_final = smoothfit.MakeSmoothHistoWithError(qvar, qvar_sm)
                        tvar_final = smoothfit.MakeSmoothHistoWithError(tvar, tvar_sm)
                    else:
                        qvar_final = smoothfit.MakeSmoothHisto(qvar, qvar_sm["nom"])
                        tvar_final = smoothfit.MakeSmoothHisto(tvar, tvar_sm["nom"])

                    qvar_final.SetNameTitle("qcd_hh_"+r+"_normY"+str(ivar)+UpDw+"__clone",   "qcd_hh_"+r+"_normY"+str(ivar)+UpDw+"__clone")
                    tvar_final.SetNameTitle("ttbar_hh_"+r+"_normY"+str(ivar)+UpDw+"__clone", "ttbar_hh_"+r+"_normY"+str(ivar)+UpDw+"__clone")

                else:
                    qvar_final = qvar.Clone("qcd_hh_"+r+"_normY"+str(ivar)+UpDw+"__clone")
                    tvar_final = tvar.Clone("ttbar_hh_"+r+"_normY"+str(ivar)+UpDw+"__clone")

                if rebinFinal is not None:
                    qvar_final = qvar_final.Rebin(len(rebinFinal)-1, qvar_final.GetName()+"_rebinFinal", rebinFinal)
                    tvar_final = tvar_final.Rebin(len(rebinFinal)-1, tvar_final.GetName()+"_rebinFinal", rebinFinal)

                if makeOutputFiles:
                    outfileStat.WriteTObject(qvar_final, "qcd_hh_normY"+str(ivar)+UpDw,"Overwrite")
                    outfileStat.WriteTObject(tvar_final, "ttbar_hh_normY"+str(ivar)+UpDw,"Overwrite")

                qvar_final.SetDirectory(0)
                tvar_final.SetDirectory(0)
                output_Dict[r]["qcd"]["normY"+str(ivar)+UpDw] = qvar_final
                output_Dict[r]["ttbar"]["normY"+str(ivar)+UpDw] = tvar_final

                
            # store some numbers for table later
            e_qcd_i = np.max( np.abs(sys_qcd) )
            e_top_i = np.max( np.abs(sys_top) )
            e_bkg_i = np.max( np.abs(sys_bkg) )


            Nbkg_SysList[r]["qcd"].append( e_qcd_i )
            Nbkg_SysList[r]["top"].append( e_top_i )
            Nbkg_SysList[r]["bkg"].append( e_bkg_i )



            
        ########################################################################################################
        ####### QCD Shape and Norm estimated from CR            ################################################
        ########################################################################################################
        if QCDSyst_Dict!=None and isMhhDistribution:  # qi
            
            qvar_shape_up = qcd_r.Clone("qvar_QCDshape_up")
            #qvar_shape_up.Multiply( QCDSyst_Dict["Shape_"+r]["fup"] )

            qvar_shape_dw = qcd_r.Clone("qvar_QCDshape_dw")
            #qvar_shape_dw.Multiply( QCDSyst_Dict["Shape_"+r]["fdw"] )

            for ibinX in range(1, qvar_shape_up.GetNbinsX()+1):
                if(qvar_shape_up.GetBinContent(ibinX) < 0):
                    qvar_shape_up.SetBinContent(ibinX, 0)
                    qvar_shape_up.SetBinError(ibinX, 0)

                if(qvar_shape_dw.GetBinContent(ibinX) < 0):
                    qvar_shape_dw.SetBinContent(ibinX, 0)
                    qvar_shape_dw.SetBinError(ibinX, 0)
                    

            qvar_shape_up.Scale( qcd_r.Integral() / qvar_shape_up.Integral() )
            qvar_shape_dw.Scale( qcd_r.Integral() / qvar_shape_dw.Integral() )
        


            ## Now do smoothing
            if do_smoothing:
                qvar_shape_up_sm = smoothfit.smoothfit(qvar_shape_up, fitFunction = smoothing_func, fitRange = qcdSmoothRange, makePlots = False, verbose = verbose,
                                                        outfileName="qcd_smoothfit_"+r+"_QCDShapeUp.root")

                qvar_shape_dw_sm = smoothfit.smoothfit(qvar_shape_dw, fitFunction = smoothing_func, fitRange = qcdSmoothRange, makePlots = False, verbose = verbose,
                                                        outfileName="qcd_smoothfit_"+r+"_QCDShapeDown.root")

                if addSmoothErrorBin:
                    qvar_shape_up_final = smoothfit.MakeSmoothHistoWithError(qvar_shape_up, qvar_shape_up_sm)
                    qvar_shape_dw_final = smoothfit.MakeSmoothHistoWithError(qvar_shape_dw, qvar_shape_dw_sm)
                else:
                    qvar_shape_up_final = smoothfit.MakeSmoothHisto(qvar_shape_up, qvar_shape_up_sm["nom"])
                    qvar_shape_dw_final = smoothfit.MakeSmoothHisto(qvar_shape_dw, qvar_shape_dw_sm["nom"])

                qvar_shape_up_final.Multiply( QCDSyst_Dict["Shape_"+r] )
                qvar_shape_dw_final.Divide( QCDSyst_Dict["Shape_"+r] )


                qvar_shape_up_final.SetNameTitle("qcd_hh_"+r+"_QCDShapeCRUp__clone",     "qcd_hh_"+r+"_QCDShapeCRUp__clone")
                qvar_shape_dw_final.SetNameTitle("qcd_hh_"+r+"_QCDShapeCRDown__clone",   "qcd_hh_"+r+"_QCDShapeCRDown__clone")


            else:
                qvar_shape_up_final = qvar_shape_up.Clone("qcd_hh_"+r+"_QCDShapeCRUp__clone")
                qvar_shape_dw_final = qvar_shape_dw.Clone("qcd_hh_"+r+"_QCDShapeCRDown__clone")


            if rebinFinal is not None:
                qvar_shape_up_final = qvar_shape_up_final.Rebin(len(rebinFinal)-1, qvar_shape_up_final.GetName()+"_rebinFinal", rebinFinal)
                qvar_shape_dw_final = qvar_shape_dw_final.Rebin(len(rebinFinal)-1, qvar_shape_dw_final.GetName()+"_rebinFinal", rebinFinal)

            if makeOutputFiles:
                outfileStat.WriteTObject(qvar_shape_up_final, "qcd_hh_QCDShapeCRUp")
                outfileStat.WriteTObject(qvar_shape_dw_final, "qcd_hh_QCDShapeCRDown")

            qvar_shape_up_final.SetDirectory(0)
            qvar_shape_dw_final.SetDirectory(0)
            output_Dict[r]["qcd"]["QCDShapeCRUp"] = qvar_shape_up_final
            output_Dict[r]["qcd"]["QCDShapeCRDown"] = qvar_shape_dw_final


        ###########################################################################################
        ### Norm comparison in CR      ############################################################
        ###########################################################################################
        if QCDSyst_Dict != None:
            
            qvar_normCR_up =  qcd_final.Clone("qcd_hh_"+r+"_QCDnormCRUp__clone")
            qvar_normCR_up.Scale( 1.0 + QCDSyst_Dict["Scale_"+r] )

            qvar_normCR_dw =  qcd_final.Clone("qcd_hh_"+r+"_QCDnormCRDown__clone")
            qvar_normCR_dw.Scale( 1.0 - QCDSyst_Dict["Scale_"+r] )

            if rebinFinal is not None:
                qvar_normCR_up = qvar_normCR_up.Rebin(len(rebinFinal)-1, qvar_normCR_up.GetName()+"_rebinFinal", rebinFinal)
                qvar_normCR_dw = qvar_normCR_dw.Rebin(len(rebinFinal)-1, qvar_normCR_dw.GetName()+"_rebinFinal", rebinFinal)

            if makeOutputFiles:
                outfileStat.WriteTObject(qvar_normCR_up, "qcd_hh_QCDNormCRUp")
                outfileStat.WriteTObject(qvar_normCR_dw, "qcd_hh_QCDNormCRDown")

            qvar_normCR_up.SetDirectory(0)
            qvar_normCR_dw.SetDirectory(0)
            output_Dict[r]["qcd"]["QCDNormCRUp"] = qvar_normCR_up
            output_Dict[r]["qcd"]["QCDNormCRDown"] = qvar_normCR_dw


            
        #####################################################################################################################
        ### top shape systematics in 4b region, if using 3b shape ###########################################################
        #####################################################################################################################
        if r == "44" and nbtag_top_shape_SRPred_for4b == "33" and MassRegionName == "SR"  and isMhhDistribution:   # qi
            ## ttbarShapeSRSyst_Dict = SystTools.ttbarShapeSysSR(topfileName,
            ##                                                     distributionName,
            ##                                                     signal_region = "22",
            ##                                                     compare_region = "33",
            ##                                                     btag_WP     = btag_WP,
            ##                                                     makePlots = True,
            ##                                                     verbose = False,
            ##                                                     outfileNameBase="TopShapeSRSysfit.root")

            ttbarShapeSRSyst_Dict = SystToolsSmooth.ttbarShapeSysSR(topfileName,
                                                                distributionName,
                                                                signal_region = "33",
                                                                compare_region = "22",
                                                                btag_WP     = btag_WP,
                                                                smoothing_func = top_smoothing_func,
                                                                SmoothRange = topSmoothRange,# (100, 2500),
                                                                makePlots = True,
                                                                verbose = False,
                                                                outfileNameBase="TopShapeSRSysfitSmooth.root")

            tvar_shape_up = top_r.Clone("tvar_ttbarShapeSR_up")
            #tvar_shape_up.Multiply( ttbarShapeSRSyst_Dict["fup"] )

            tvar_shape_dw = top_r.Clone("tvar_ttbarShapeSR_dw")
            #tvar_shape_dw.Multiply( ttbarShapeSRSyst_Dict["fdw"] )


            for ibinX in range(1, tvar_shape_up.GetNbinsX()+1):
                if(tvar_shape_up.GetBinContent(ibinX) < 0):
                    tvar_shape_up.SetBinContent(ibinX, 0)
                    tvar_shape_up.SetBinError(ibinX, 0)

                if(tvar_shape_dw.GetBinContent(ibinX) < 0):
                    tvar_shape_dw.SetBinContent(ibinX, 0)
                    tvar_shape_dw.SetBinError(ibinX, 0)
                    

            tvar_shape_up.Scale( top_r.Integral() / tvar_shape_up.Integral() )
            tvar_shape_dw.Scale( top_r.Integral() / tvar_shape_dw.Integral() )


            ## Now do smoothing ##########################
            if do_smoothing:
                tvar_shape_up_sm = smoothfit.smoothfit(tvar_shape_up, fitFunction = top_smoothing_func, fitRange = topSmoothRange, makePlots = False, verbose = verbose,
                                                        outfileName="top_smoothfit_"+r+"_ttbarShapeSRUp.root")

                tvar_shape_dw_sm = smoothfit.smoothfit(tvar_shape_dw, fitFunction = top_smoothing_func, fitRange = topSmoothRange, makePlots = False, verbose = verbose,
                                                        outfileName="top_smoothfit_"+r+"_ttbarShapeSReDown.root")

                if addSmoothErrorBin:
                    tvar_shape_up_final = smoothfit.MakeSmoothHistoWithError(tvar_shape_up, tvar_shape_up_sm)
                    tvar_shape_dw_final = smoothfit.MakeSmoothHistoWithError(tvar_shape_dw, tvar_shape_dw_sm)
                else:
                    tvar_shape_up_final = smoothfit.MakeSmoothHisto(tvar_shape_up, tvar_shape_up_sm["nom"])
                    tvar_shape_dw_final = smoothfit.MakeSmoothHisto(tvar_shape_dw, tvar_shape_dw_sm["nom"])

                tvar_shape_up_final.Multiply( ttbarShapeSRSyst_Dict["Shape"] )
                tvar_shape_dw_final.Divide( ttbarShapeSRSyst_Dict["Shape"] )

                tvar_shape_up_final.SetNameTitle("ttbar_hh_"+r+"_ttbarShapeSRUp__clone",     "ttbar_hh_"+r+"_ttbarShapeSRUp__clone")
                tvar_shape_dw_final.SetNameTitle("ttbar_hh_"+r+"_ttbarShapeSRDown__clone",   "ttbar_hh_"+r+"_ttbarShapeSRDown__clone")


            else:
                tvar_shape_up_final = tvar_shape_up.Clone("ttbar_hh_"+r+"_ttbarShapeSRUp__clone")
                tvar_shape_dw_final = tvar_shape_dw.Clone("ttbar_hh_"+r+"_ttbarShapeSRDown__clone")


            if rebinFinal is not None:
                tvar_shape_up_final = tvar_shape_up_final.Rebin(len(rebinFinal)-1, tvar_shape_up_final.GetName()+"_rebinFinal", rebinFinal)
                tvar_shape_dw_final = tvar_shape_dw_final.Rebin(len(rebinFinal)-1, tvar_shape_dw_final.GetName()+"_rebinFinal", rebinFinal)

            if makeOutputFiles:
                outfileStat.WriteTObject(tvar_shape_up_final, "ttbar_hh_ttbarShapeSRUp")
                outfileStat.WriteTObject(tvar_shape_dw_final, "ttbar_hh_ttbarShapeSRDown")

            tvar_shape_up_final.SetDirectory(0)
            tvar_shape_dw_final.SetDirectory(0)
            output_Dict[r]["ttbar"]["ttbarShapeSRUp"] = tvar_shape_up_final
            output_Dict[r]["ttbar"]["ttbarShapeSRDown"] = tvar_shape_dw_final

            


        
        ### close outfiles, if used ###
        if makeOutputFiles:
            outfileStat.Close()

    ### Print tables ###
    #PrintTable( Nbkg_dict, Nbkg_SysList, regions)
    #print vartxt

    #print output_Dict

    output_Dict['regions'] = regions

    return output_Dict


def FuncSum(x):
    return ( func1.Eval(x[0]) + func2.Eval(x[0]))





def PrintTable( Nbkg_dict, Nbkg_SysList, Regions):

    
    e_qcd_tot = {}
    e_top_tot = {}
    e_bkg_tot = {}

    for iR in Regions:
        e_qcd_tot[iR] = 0
        e_top_tot[iR] = 0
        e_bkg_tot[iR] = 0

        for ierr in range(len(Nbkg_SysList[iR]["qcd"])):
            e_qcd_tot[iR] = e_qcd_tot[iR] + Nbkg_SysList[iR]["qcd"][ierr]**2
            e_top_tot[iR] = e_top_tot[iR] + Nbkg_SysList[iR]["top"][ierr]**2
            e_bkg_tot[iR] = e_bkg_tot[iR] + Nbkg_SysList[iR]["bkg"][ierr]**2

        e_qcd_tot[iR] = np.sqrt(e_qcd_tot[iR])
        e_top_tot[iR] = np.sqrt(e_top_tot[iR])
        e_bkg_tot[iR] = np.sqrt(e_bkg_tot[iR])


    columnStructure = '| l |'
    for ic in range(len(Regions)):
        columnStructure = columnStructure + ' c |'

        
    outtext = ''
    outtext  = outtext + ' \n'
    outtext  = outtext + ' \n'
    outtext  = outtext + '\\begin{table}[htbp!] \n'
    outtext  = outtext + '\\begin{center} \n'
    outtext  = outtext + '\\begin{tabular}{' + columnStructure + ' } \n'
    outtext  = outtext + '\\hline \n'
    outtext  = outtext + ' Sample '
    for iR in Regions:
        outtext  = outtext + ' & ' + iR[1] + 'b SR Prediction '
    outtext  = outtext + ' \\\\ \n'
    
    outtext  = outtext + '\\hline \n'
    outtext  = outtext + '\\hline \n'
    
    outtext  = outtext + 'QCD '
    for iR in Regions:
        outtext  = outtext + ' & ' + str(float('%.3g' % Nbkg_dict[iR]["qcd"] )) + ' $\pm$ ' + str(float('%.3g' % e_qcd_tot[iR] ))
    outtext  = outtext + ' \\\\ \n'
    
    outtext  = outtext + '$ t \\bar{t}$ '
    for iR in Regions:
        outtext  = outtext + ' & ' + str(float('%.3g' % Nbkg_dict[iR]["top"] )) + ' $\pm$ ' + str(float('%.3g' % e_top_tot[iR] ))
    outtext  = outtext + ' \\\\ \n'

    
    outtext  = outtext + '\\hline \n'
    outtext  = outtext + 'Total '
    for iR in Regions:
        outtext  = outtext + ' & ' + str(float('%.3g' % Nbkg_dict[iR]["bkg"] )) + ' $\pm$ ' + str(float('%.3g' % e_bkg_tot[iR] ))
    outtext  = outtext + ' \\\\ \n'
    
    outtext  = outtext + '\\hline \n'
    outtext  = outtext + '\\hline \n'
    outtext  = outtext + 'Data '
    for iR in Regions:
        outtext  = outtext + ' & ' + ' [BLINDED] '
    outtext  = outtext + ' \\\\ \n'


    outtext  = outtext + '\\hline \n'
    outtext  = outtext + '\\end{tabular}  \n'
    outtext  = outtext + '\\caption{Background predictions in SR}  \n'
    outtext  = outtext + '\\label{tab:boosted-SR-yields-wsys}  \n'
    outtext  = outtext + '\\end{center}  \n'
    outtext  = outtext + '\\end{table}  \n'
    outtext  = outtext + '  \n'
    outtext  = outtext + '  \n'

    print outtext

if __name__=="__main__":
    HistoAnalysis()












##     pred_final = qcd_final.Clone("pred_final__"+r)
##     pred_final.Add( top_final )


##     func1 = qcd_sm["nom"]
##     func2 = top_sm["nom"]

##     pred_sm = R.TF1("pred_sm", FuncSum, 900, 3000)

##     pred_sm.Draw("same")
##     top_sm["nom"].Draw("same")

##     pred_final_raw = qcd_r.Clone("qcd_final_raw__"+r)
##     pred_final_raw.Add(top_r)

##     outfile = R.TFile("outfile_"+r+".root","RECREATE")

##     c=R.TCanvas()
##     pred_final_raw.Draw("HIST")
##     top_r.SetLineColor(R.kBlack)
##     top_r.SetFillColor(R.kGreen)
##     top_r.Draw("sameHIST")

##     pred_sm.Draw("same")
##     top_sm["nom"].Draw("same")

##     c.Write()

##     c=R.TCanvas()

##     pred_final.Draw("HIST")

##     top_final.SetLineColor(R.kBlack)
##     top_final.SetFillColor(R.kGreen)

##     top_final.Draw("sameHIST")

##     c.Write()

##     outfile.Close()

