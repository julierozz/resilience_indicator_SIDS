import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines

import pandas as pd
import numpy as np

from fancy_plots import savefig

############################################################################# 
#######################         FROM SVG              ####################### 
#############################################################################     
    
from bs4 import BeautifulSoup    
from IPython.display import Image, display, HTML, SVG
img_width = 400

import os, shutil
from subprocess import Popen, PIPE, call 

#Default options for plots: 
#this controls the font used in the legend
font = {'family' : 'sans serif',
    'size'   : 22}
plt.rc('font', **font)

def make_map_from_svg(series_in, svg_file_path, outname, bins=None, bincolors=None, color_maper=None, label = "", outfolder ="img/" , new_title="", verbose=False, font=font, doPNG=True,formater=".0f", keepSVG=False, no_data_color= "#e0e0e0"  ):
    """Makes a cloropleth map and a legend from a panda series and a blank svg map. 
    Assumes the index of the series matches the SVG classes
    Saves the map in SVG, and in PNG if Inkscape is installed.
    if provided, new_title sets the title for the new SVG map
    """
    
    if (color_maper is not None) and (bins is not None) and (color_maper is not None):
        print("Error: provide either (bins and bincolors) or a color_maper, but not both")
        return
        
        
    #compute the colors from a color mapper or just bins 
    if color_maper is not None:
        color = data_to_rgb(series_in,color_maper=color_maper)
        is_bined = False
    elif (bins is not None) and (bincolors is not None):
        
        if type(bins)==int: #if number of bins was provided
            eps = 1e-5
            bins = np.linspace(series_in.min()*(1-eps),series_in.max()*(1+eps),bins+1)

        color = pd.cut(series_in, bins, labels=bincolors)
        is_bined = True
    else:
        print("Error: provide either (bins AND bincolors) or a color_maper, but not both")
        return
    
    
    #output file name
    filename =("map_of_" if doPNG else "")+outname
    target_name = outfolder+filename

    #read input 
    with open(svg_file_path, 'r',encoding='utf8') as svgfile: #MIND UTF8
        soup=BeautifulSoup(svgfile.read(),"xml")
        
        
    for p in soup.findAll("path"):
        c=p["class"] 
        if p.has_attr('id'):
            # print("found")
            c+=" "+p["id"]
        if ("data" in c) or ('country' in c):
            iso_code = c[-3:] #guesses the ISO code from the class (too specific)
            try:
                p["style"]  = "fill: {fill_color};".format(fill_color=color[iso_code])
            except:
                # p["style"]  = "fill: #ff0000;"
                pass

                
    #write output
    with open(target_name+".svg", 'w', encoding="utf-8") as svgfile:
        svgfile.write(soup.prettify())
          
    if keepSVG:
        #Link to SVG
        display(HTML("<a target='_blank' href='"+target_name+".svg"+"'>SVG "+new_title+"</a>"))  #Linking to SVG instead of showing SVG directly works around a bug in the notebook where style-based colouring colors all the maps in the NB with a single color scale (due to CSS)
    
    
    
    # reports missing data (TO BE RECODED)       
    # if verbose:        
        # places_in_soup = [p["class"] for p in soup.findAll("path")]        
        # data_missing_in_svg = series_in[~series_in.index.isin(places_in_soup)].index.tolist()
        # data_missing_in_series = [p for p in places_in_soup if (p not in series_in.index.tolist())]
        
        # if data_missing_in_svg:
            # print("Missing in SVG: "+"; ".join(set(data_missing_in_svg)))
        # if data_missing_in_series:
            # print("Missing in series: "+"; ".join(set(data_missing_in_series)))

    if shutil.which("inkscape") is None:
        print("cannot convert SVG to PNG or PDF. Install Inkscape to do so.")
        could_do_png_map = False
    else:
        if doPNG:
            #Attempts to inkscape SVG to PNG    
            process=Popen("inkscape -f {map}.svg -e {map}.png -d 150".format(map=target_name, outfolder = outfolder) , shell=True, stdout=PIPE,   stderr=PIPE)
            out, err = process.communicate()
            errcode = process.returncode
            if errcode:
                could_do_png_map = False
                print("Could not transform SVG to PNG. Error message was:\n"+err.decode())
            else:
                could_do_png_map = True
                #trims margins out
                call("convert {map}.png -trim {map}.png".format(map=filename), shell=True, cwd=outfolder)

                display(HTML("<a target='_blank' href='"+target_name+".png"+"'>PNG "+new_title+"</a>"))  
        
        #Attempts to inkscape SVG to PDF
        process=Popen('inkscape -f "{map}.svg" --verb=FitCanvasToDrawing --export-pdf "{map}.pdf"'.format(map=target_name) , shell=True, stdout=PIPE,   stderr=PIPE)
        out, err = process.communicate()
        errcode = process.returncode
        if errcode:
            could_do_pdf_map = False
            print("Could not transform SVG to pdf. Error message was:\n"+err.decode())
        else:
            could_do_pdf_map = True
            display(HTML("<a target='_blank' href='"+target_name+".pdf"+"'>PDF "+new_title+"</a>"))  #Linking to SVG instead of showing SVG directly works around a bug in the notebook where style-based colouring colors all the maps in the NB with a single color scale (due to CSS)

    #deletesSVG if not keeping them (SVGs are very heavy sometimes)        
    if could_do_pdf_map:
        if not keepSVG:
            os.remove(target_name+".svg")


        #crops the resulting pdf    
        call('pdfcrop "{map}.pdf" "{map}.pdf"'.format(map=target_name))
            
    #makes the legend with matplotlib
    if doPNG:
        if is_bined: 
            l = make_bined_legend(series_in,bincolors,bins,label,font,outfolder+"legend_of_"+outname, formater=formater, no_data_color = no_data_color)
        else:
            l = make_legend(series_in,color_maper,label,outfolder+"legend_of_"+outname)
    
        if shutil.which("convert") is None:
            print("Cannot merge map and legend. Install ImageMagick® to do so.")
        elif could_do_png_map:
            
            
            #Attempts to downsize to a single width and concatenate using imagemagick
            # call("convert "+outfolder+"legend_of_{outname}.png -resize {w} small_legend.png".format(outname=outname,w=img_width), shell=True )
            # call("convert "+outfolder+"map_of_{outname}.png -resize {w} small_map.png".format(outname=outname,w=img_width) , shell=True)
            
            merged_path = "map_and_legend_of_{outname}.png".format(outname=outname)
            
            # call("convert -append small_map.png small_legend.png "+merged_path, shell=True)
            
            if is_bined:
                call("convert map_of_{outname}.png legend_of_{outname}.png -background none +append ".format(outname=outname)+merged_path, cwd=outfolder, shell=True)
            else:
                call("convert map_of_{outname}.png -gravity east legend_of_{outname}.png -background none -append ".format(outname=outname)+merged_path, cwd=outfolder, shell=True)
        
        #removes temp files
        if os.path.isfile("small_map.png"):
            os.remove("small_map.png")
        if os.path.isfile("small_legend.png"):
            os.remove("small_legend.png")

        if os.path.isfile(outfolder+merged_path):
            return Image(outfolder+merged_path)
        
    
import matplotlib as mpl

def make_legend(serie,cmap,label="",path=None):
    #todo: log flag
    
    plt.rc('font', **font)
    
    fig = plt.figure(figsize=(8,3))
    ax1 = fig.add_axes([0.05, 0.80, 0.9, 0.15])

    vmin=serie.min()
    vmax=serie.max()

    #continuous legend
    norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)

    cb = mpl.colorbar.ColorbarBase(ax1, cmap=cmap, norm=norm, orientation='horizontal')
    #cb.ax.set_xticklabels(['0.01%','0.1%','1%','10%'])
    cb.set_label(label)
    if path is not None:
        savefig(path,transparent=True)  
    plt.close(fig)    
    
    
    return Image(path+".png", width=img_width   )  
    
    
def make_bined_legend(serie,bincolors,bins,label="",font=font,path=None, figsize=(9,9), formater=".0f", no_data_color = "#e0e0e0"):
    #todo: log flag
    plt.rc('font', **font)
    
    patches =[]
    for i in np.arange(len(bincolors)):
        patches+=[mpatches.Patch( fc=bincolors[i], 
                    label=("{m:"+formater+"} — {M:"+formater+"}").format(m=bins[i],M=bins[i+1])
                        )]
    
    patches+=[mpatches.Patch( fc=no_data_color, 
                    label="No data"
                        )]
    
    fig=plt.figure(figsize=figsize)
    ax=plt.gca()

    ax.legend(handles=patches, loc="upper left", prop=font,frameon=False, title=label)  

    ax.axis('off')

    if path is not None:
        savefig(path,transparent=True)  
    plt.close(fig)    
    
    return Image(path+".png", width=img_width   )  

    
def n_to_one_normalizer(s,n=0):
  #affine transformation from s to [n,1]      
    y =(s-s.min())/(s.max()-s.min())
    return n+(1-n)*y
    
def bins_normalizer(x,n=7):
  #bins the data in n regular bins ( is better than pd.bin ? )     
    n=n-1
    y= n_to_one_normalizer(x,0)  #0 to 1 numbe
    return np.floor(n*y)/n

def quantile_normalizer(column, nb_quantile=5):
  #bbins in quintiles      
    return (pd.qcut(column, nb_quantile,labels=False))/(nb_quantile-1)

def num_to_hex(x):
    h = hex(int(255*x)).split('x')[1]
    if len(h)==1:
        h="0"+h
    return h

def data_to_rgb(serie,color_maper=plt.cm.get_cmap("Blues_r"), normalizer = n_to_one_normalizer, norm_param = 0, na_color = "#e0e0e0"):
    """This functions transforms  data series into a series of color, using a colormap."""

    data_n = normalizer(serie,norm_param)
    
    #here matplolib color mappers will just fill nas with the lowest color in the colormap
    colors = pd.DataFrame(color_maper(data_n),index=serie.index, columns=["r","g","b","a"]).applymap(num_to_hex)
    
    out = "#"+colors.r+colors.g+colors.b
    out[serie.isnull()]=na_color
    return out.str.upper()
    
    
    