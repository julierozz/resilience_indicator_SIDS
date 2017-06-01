from progress_reporter import *
import matplotlib.pyplot as plt

from subprocess import Popen  #to call other programs from python
import sys #one function, flush, to force jupyter to print a message immediately
import glob  #to make foldeltas, move files, etc.

import pandas as pd
from res_ind_lib import *
from fancy_plots import autolabel, savefig

import datetime


#height of the bars
height = 0.40  

#fonts
font = {'family' : 'sans serif','size'   : 11}
smallfont= {'family' : 'sans serif','size'   : 9}
tinyfont= {'family' : 'sans serif','size'   : 8}

#instructs matplotlib to use that font by default
plt.rc('font', **font)
 
        
def render_pol_cards(deltas,colors,policy_descriptions,unit,list_of_cards_to_plot, 
outfolder="cards/", name_suffix="", max_lines = None, do_by_policy = False ,offset_vertical = 3, use_arrows=False , use_title = True       ):
    """Render package cards
    
    -deltas: dataframe indexed by economies. Column is multi-indexed: policies x ["dWtot_currency","dKtot"]  (this function is actually hardcoded and does needs these two outputs in deltas). The impact of policies on dw and dK per economy.
    
    -policy_descriptions. Series index by policies (columns in deltas). Explains what the policy is. eg "Decrease poverty to 0.1%" 
    
    -colors: dataframe. Columns: ["dWtot_currency","dKtot"]. Rows: kwargs to pass to plt.barh for formatting the color bars.
    
    -unit: dictionary such as {"multiplier":1000, "string" Thousands }. For the x label.
    list_of_cards_to_plot: collection of economies or policies to plot. Should be in deltas.index.
    """
    
    #replaces policy code with policy description
    deltas = deltas.rename(columns = policy_descriptions)

    if do_by_policy:
        deltas = deltas.T.unstack("outputs")
        list_of_cards_to_plot = policy_descriptions[list_of_cards_to_plot]
        
    
    #list of outputs to use as metrics
    assess_set = ["dKtot", "dWtot_currency",]

    for p in list_of_cards_to_plot:
        #Displays current province in the loop 
        progress_reporter(p)    
        
        #select current line in deltas, and scales it.
        toplot = unit["multiplier"]*deltas.ix[p].dropna().unstack("outputs")  
        
        #assumes the policy is framed in terms of what increases welfare ("decrease poverty", not "increase poverty")

        # toplot = -toplot
        # toplot = toplot[assess_set].sort_values("dWtot_currency",ascending=False)
        
        toplot = toplot[assess_set].sort_values("dWtot_currency",ascending=True)
        
        #keep only upper lines if needed
        if max_lines is not None:
            toplot = toplot.tail(max_lines)
        
        #number of policy experiments to render
        n=toplot.shape[0]
        
        #new figure
        fig, ax = plt.subplots(figsize=(3.5,n/2))
    
        #actual plotting
        ind=np.arange(n)
            
        nb_h=0    
        for out in assess_set:
            
            rects1 = ax.barh(ind+nb_h*height,toplot[out],height=height, **colors.ix[out]
            #labels (numbers) on the bars
                            )

            autolabel(ax,rects1,colors.ix[out,"edgecolor"],2,**tinyfont)
            # autolabel(ax,rects2,colors.ix["dWtot_currency","edgecolor"],2,**smallfont)
            nb_h+=1

        #0 line
        plt.vlines(0, 0, n, colors="black")    
        
        # add some labels, title and axes ticks
        ax.set_xlabel(unit["string"])
        ax.set_yticks(ind+height)
        ax.set_yticklabels(toplot.index+ "     ")#pad for labels
        
        if use_title:
            plt.title(p)    

        # remove spines
        # ax.spines['bottom'].set_color('none')
        ax.spines['right'].set_color('none')

        ax.spines['top'].set_color('none')
        ax.spines['left'].set_color("none")

        #removes ticks 
        for tic in ax.xaxis.get_major_ticks() + ax.yaxis.get_major_ticks():
            tic.tick1On = tic.tick2On = False
        
        ax.xaxis.set_ticklabels([])

        arrow_on_bottom = True
        
        if use_arrows:
            #annotated "legend"
            ax.annotate("Avoided asset losses",
                xy=(toplot.iloc[1 if arrow_on_bottom else -1]["dKtot"]+offset_vertical,
                height/2 if arrow_on_bottom else n-1+height/2),
                xycoords='data',ha="left",va="center",
              xytext=(20, 3 if arrow_on_bottom else -5), textcoords='offset points', 
                arrowprops=dict(arrowstyle="->",
            connectionstyle="arc3,rad=+0.13",color=colors.edgecolor.dKtot
                    ), clip_on=False, **smallfont)

            ax.annotate("Avoided well-being losses",  xy=(toplot.iloc[1 if arrow_on_bottom else -1]["dWtot_currency"]+offset_vertical,3*height/2 if arrow_on_bottom else n-height),xycoords='data',ha="left",va="center",
                          xytext=(20,8 if arrow_on_bottom else  3), textcoords='offset points', 
                            arrowprops=dict(arrowstyle="->",
                                            connectionstyle="arc3,rad=+0.13",color=colors.edgecolor.dWtot_currency
                                            ), clip_on=False,  **smallfont)

        
        glob.os.makedirs(outfolder,exist_ok=True)
        #exports to pdf
        savefig(outfolder+file_name_formater(p)+name_suffix)
        plt.close()    
        
        
    
    progress_reporter("done at "+ str(datetime.datetime.now()))
    return fig
    
    
def file_name_formater(string):
    """Ensures string does not contain special characters so it can be used as a file name"""    
    return string.lower().replace(" ","_").replace("\\","")
       

def merge_cardfiles(list,outputname):
    """Merges individual policy card pdf to a single multi page pdf with all the cards. Requires ghostscipt."""
    #implements http://stackoverflow.com/questions/7102090/combining-pdf-files-with-ghostscript-how-to-include-original-file-names

    #builds the command for ghostscript
    command= ""
    i=1
    for name in list:
        command+="({name}) run [ /Page {page} /Title ({simplename}) /OUT pdfmark \n".format(name=name.replace("\\","/"),simplename=glob.os.path.splitext(glob.os.path.basename(name))[0].replace("_"," ").title(),page=i)
        i+=1

    #writes the command for ghostscipt
    with open("control.ps", "w") as text_file:
        text_file.write(command)

    #runs ghostscipt in a new process
    p=Popen("gswin64c -dEPSFitPage -sDEVICE=pdfwrite -o "+outputname+" control.ps");

    print("Merging cards....")
    sys.stdout.flush()

    #waits for GS to finish
    p.communicate()
    print("Merging cards done")
    
    #deletes GS command
    glob.os.remove("control.ps")

def convert_pdf_to_png(folder):
    """Convert individual pdf cards to PNG. Requires imagemagick. 
    Moves the resulting png to a subolfer""" 
    
    folder = glob.os.path.dirname(folder)
        
    #creates the destination subdir
    destinationpath =glob.os.path.join(folder,"png") 
    glob.os.makedirs(destinationpath,exist_ok=True) 
    
    #starts imagemagick in a new process 
    q=Popen("mogrify -density 150 -path {dest} -format png {folder}/*.pdf".format(folder=folder, dest=destinationpath));
    print("Converting cards....")
    sys.stdout.flush()
    
    #waits for imagemagick to finish
    q.communicate()
    print("conversion to png done")


def changed_lines(a,b, output="string", tol=1e-5):
    change = (2*(a-b)/(a+b)).abs().mean()
    changed =change[change>tol].index

    #returns list of variables that have changed
    if output=="index":
        return changed

    #returns summary string
    else:
        
        #summary string
        if len(changed)>0 :
            sum_string = " ".join(change[changed].to_string(float_format= lambda x: "(~{:.1%})".format(x)).replace("\n","; ").split())+"." 
        else:
            sum_string = "none."
    
        
        if output == "string":   
            return sum_string 
        elif output == "both":   
            return changed, sum_string 
        else:
            raise Exception("Unrecognised output option. Expected 'string' or 'index' or 'both'.")
    
        



        
    
