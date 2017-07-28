from pandas_helper import *
from res_ind_lib import *

def apply_policy(m_,c_,h_, a_ , policy_name=None, verbose=True):
    """Choses a policy by name, appliesit to m,c,and/or h, and returns new values as well as a policy description"""    
    
    #duplicate inputes
    m=m_.copy(deep=True)
    c=c_.copy(deep=True)
    h=h_.copy(deep=True)
    a=a_.copy() #dictionary, do not attempt to deep copy
    
    
    if policy_name is None:
        desc = "Baseline"
        
    # Pov reduction
    elif policy_name=="kp":
        c.k = c.k.unstack().assign(poor=lambda df:df.poor*1.1).stack()
        desc = "Increase\nincome of the\npoor 10%"    # Pov reduction
    
    elif policy_name=="pov_head":
        c.n = c.n.unstack().assign(poor=.18, nonpoor=.82).stack()
        desc = "Reduce poverty from 20% to 18%"
        
    #Borrow abi
    elif policy_name=="borrow_abi":
        m.borrow_abi = m.borrow_abi.clip(lower=1)
        desc = "Develop contingent finance and reserve funds"

    #Scale up abi
    elif policy_name=="prepare_scaleup":
        m.prepare_scaleup = 1
        desc = "Make social protection scalable after a shock"
    
    #Early warnings to 1, except for earthquake
    elif policy_name=="shew":
        h.shew =1
        h.shew=h.shew.unstack("hazard").assign(earthquake=0).stack("hazard").reset_index().   set_index(event_level+[ "income_cat"])
        desc = "Universal\naccess to early\nwarnings"

    #reconstruction to 2.5 years
    elif policy_name=="T_rebuild_K":
        m.T_rebuild_K = 2
        desc = "Accelerate\nreconstruction\n(by 33%)"

    #social_p needs to be at least 50%
    elif policy_name=="social_p":
        
        m,c=clip_social_p(m,c,fun=lambda x: x.clip(lower=.33)   )
        # ) 
        desc = "Increase social\ntransfers to poor\npeople to at\nleast 33%"
        
    elif policy_name=="axfin":
        c.axfin=1
        desc = "Universal\naccess to\nfinance"
        
    #vpoor = vnonpoor
    elif policy_name=="vpvr":
        c.v = c.v.unstack().assign(poor=lambda x:x.nonpoor).stack()
        desc = "Make poor people's assets as resistant as nonpoor people's assets"    
        
    #30% or poor people see their v reduced 30% (not 10pts!!)   
    elif policy_name=="vp":
        n = c.n.unstack().poor
        dv = .3 #reduction in v
        f =.05 #fractionof nat pop would get the reduction
        
        c.v = c.v.unstack().assign(poor=lambda df:(df.poor*(1-dv*f/n))).stack().clip(lower=0)         
        
        desc = "Reduce asset\nvulnerability\n(by 30%) of\npoor people\n(5% of the population)"
        
    #10% or nonpoor people see their v reduced 30%    
    elif policy_name=="vr":
        n = c.n.unstack().nonpoor
        dv = .3 #reduction in v
        f =.05 #fractionof nat pop would get the reduction
        c.v = c.v.unstack().assign(nonpoor=lambda x:(x.nonpoor*(1-dv*f/n))).stack().clip(lower=0)
        desc = "Reduce asset\nvulnerability\n(by 30%) of\nnonpoor people\n(5% of the population)"
    
    #10% or poor people see their fA reduced 10%    
    elif policy_name=="fap":
        n = 0.2
        dfa = .05 #reduction in fa
        
        h["n"] = h.assign(n=1).n.unstack().assign(poor=0.2,nonpoor=0.8).stack()
        fa_event = agg_to_event_level(h,"fa")
        
        h = h.drop("n",axis=1)
        
        h.fa = h.fa.unstack().assign(poor=lambda x:(x.poor-dfa*fa_event/n)).stack().clip(lower=0)
        desc = "Reduce exposure\nof the poor by 5%\nof total exposure"

       
        
    #10% or NONpoor people see their fA reduced 10%    
    elif policy_name=="far":
        n = 0.8
        dfa =.05 #fractionof nat pop would get the reduction

        h["n"] = h.assign(n=1).n.unstack().assign(poor=0.2,nonpoor=0.8).stack()
        fa_event = agg_to_event_level(h,"fa")
        
        h.fa = h.fa.unstack().assign(nonpoor=lambda x:(x.nonpoor-dfa*fa_event/n)).stack().clip(lower=0)
        desc =  "Reduce\nexposure of the nonpoor by 5%\nof total exposure"

    #Exposure equals to nonpoor exposure (mind that exposure in cat_info is OVERWRITTEN by exposure in h)
    elif policy_name=="fapfar":
        h.fa = h.fa.unstack().assign(poor=lambda x:x.nonpoor).stack()
        desc = "Make poor people's exposure the same as the rest of population"
    
    elif policy_name=="prop_nonpoor":
        a.update(optionPDS = "prop_nonpoor", optionT="perfect",optionB="unlimited",optionFee="insurance_premium", share_insured=.25)
        desc = "Develop market\ninsurance\n(nonpoor people)"
    
    elif policy_name=="prop_nonpoor_lms":
        a.update(optionPDS = "prop_nonpoor_lms", optionT="prop_nonpoor_lms",optionB="unlimited",optionFee="insurance_premium", share_insured=.5)
        desc = "Develop market insurance (25% of population, only nonpoor)"
    
    
    elif policy_name=="PDSpackage":
        m,c,h,a,desc = apply_policy(m,c,h,a,"borrow_abi")
        m,c,h,a,desc = apply_policy(m,c,h,a,"prepare_scaleup")
        
        desc = "Postdisaster\nsupport\npackage"    
        
    elif policy_name=="ResiliencePackage":
        m,c,h,a,desc = apply_policy(m,c,h,a,"PDSpackage")
        m,c,h,a,desc = apply_policy(m,c,h,a,"axfin")
        m,c,h,a,desc = apply_policy(m,c,h,a,"T_rebuild_K")
        m,c,h,a,desc = apply_policy(m,c,h,a,"social_p")
        m,c,h,a,desc = apply_policy(m,c,h,a,"prop_nonpoor_lms")
        desc = "Resilience package"
    
    
    elif policy_name=="ResiliencePlusEW":
        m,c,h,a,desc = apply_policy(m,c,h,a,"ResiliencePackage")
        m,c,h,a,desc = apply_policy(m,c,h,a,"shew")
        
        desc = "Resilience Package + Early Warning Package"
        
    elif policy_name=="Asset_losses" :   
        m,c,h,a,desc = apply_policy(m,c,h,a,"fap")
        m,c,h,a,desc = apply_policy(m,c,h,a,"far")
        m,c,h,a,desc = apply_policy(m,c,h,a,"vp")
        m,c,h,a,desc = apply_policy(m,c,h,a,"vr")
        m,c,h,a,desc = apply_policy(m,c,h,a,"shew")
        
        desc = "Asset losses package "
        
    elif policy_name=="Asset_losses_no_EW":    
        m,c,h,a,desc = apply_policy(m,c,h,a,"fap")
        m,c,h,a,desc = apply_policy(m,c,h,a,"far")
        m,c,h,a,desc = apply_policy(m,c,h,a,"vp")
        m,c,h,a,desc = apply_policy(m,c,h,a,"vr")
        desc = "Asset losses package (excluding early warnings)"
        
    elif policy_name=="":
        pass
    
    if verbose:
        print(desc)
    
    return m,c,h, a, desc
 
 
 
def clip_social_p(m,c,fun=lambda x: x.clip(lower=.50)   ) :
        """Compute social p from cat_info (c) and macro (m).
        Then changes social p to something applying fun  
            for instance fun=lambda x:.3333 will set social_p at .3333
            fun = lambda x: x.clip(lower=.50) gets social p at least at 50% 
        """
        
        m = m.copy(deep=True)
        c = c.copy(deep=True)
        
        #############
        #### preparation

        #current conso and share of average transfer
        cp  = c.c.ix[:,"poor"]
        gsp = c.gamma_SP.ix[:,"poor"]
        cp.head()

        #social_p
        cur_soc_sh = gsp* m.gdp_pc_pp  *m.tau_tax /cp
        cur_soc_sh.head()

        #social_p needs to be at least 50%
        obj_soc_sh  = fun(cur_soc_sh)
        # obj_soc_sh.sample(10)

        # increase of transfer for poor people
        money_needed = (obj_soc_sh*(1-cur_soc_sh)/(1-obj_soc_sh)-cur_soc_sh)*cp
        money_needed.head()

        #financing this transfer with a tax on the whole population
        nu_tx = (m.gdp_pc_pp*m.tau_tax+money_needed*c.n.ix[:,"poor"])/m.gdp_pc_pp
        nu_tx.head();

        #increasing the share of avg transfer that goes to poor
        nu_gsp = (money_needed+cur_soc_sh*cp)/(m.gdp_pc_pp*nu_tx)

        #balancing with less for nonpoor
        nu_gs = (1-0.2*nu_gsp)/0.8
        nu_gs;
            
        #double checking that that the objectife of 50% at least has been met
        # new_soc_sh = nu_gsp* m.gdp_pc_pp  *nu_tx /(cp+money_needed)
        # ((new_soc_sh-obj_soc_sh)**2).sum()

        #updating c and m
        c.gamma_SP = concat_categories(nu_gsp,nu_gs,index=income_cats);
        m.tau_tax = nu_tx
         
        return m,c 


