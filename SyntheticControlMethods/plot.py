# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import, division, print_function

import numpy as np
#import warning

#class PlotWarning(UserWarning):
#    '''Custom warning class for warnings related to plotting'''
#    pass

class Plot(object):
    '''
    Class responsible for all plotting functionality in package
    '''

    def plot(self, panels, figsize=(15, 12), 
            treated_label="Treated Unit",
            synth_label="Synthetic Control",
            treatment_label="Treatment",
            in_space_exclusion_multiple=5):
        '''
        Supported plots:
          original:
            Outcome of the treated unit and the synthetic control unit for all time periods

          pointwise:
            Difference between the outcome of the treated and synthetic control unit
            I.e. same as original but normalized wrt. the treated unit
          
          cumulative:
            Sum of pointwise differences in the post treatment period
            I.e. the cumulative treatment effect

          in-space placebo:
            Pointwise plot of synthetic control and in-space placebos
            
            Procedure:
            Fits a synthetic control to every control unit. 
            These synthetic controls are referred to "in-space placebos"

          pre/post rmspe:
            Histogram showing 
            (post-treatment rmspe) / (pre-treatment rmspe) 
            for real synthetic control and all placebos

            Extreme values indicates small difference in pre-period with 
            large difference (estimated treatment effect) in the post-period
            Treated unit should be more extreme than placebos to indicate significance


        Arguments:
          panels : list of strings
            list of the plots to be generated
        
          figsize : tuple (int, int)
            argument to plt.figure
            First value indicated desired width of plot, second the height
            The height height is divided evenly between each subplot, whereas each subplot has full width
            E.g. three plots: each subplot will have figure size (width, height/3)
           
          treated_label : str
            Label for treated unit in plot title and legend
        
          synth_label : str
            Label for synthetic control unit in plot title and legend

          in_space_exclusion_multiple : float
            default: 5
            used only in 'in-space placebo' plot. 
            excludes all placebos with PRE-treatment rmspe greater than 
            the real synthetic control*in_space_exclusion_multiple

        Returns:

        '''

        #Extract Synthetic Control
        synth = self.synth_outcome
        time = self.dataset[self.time].unique()

        plt = self._get_plotter()
        fig = plt.figure(figsize=figsize)
        valid_panels = ['original', 'pointwise', 'cumulative', 
                        'in-space placebo', 'pre/post rmspe', 'in-time placebo']
        solo_panels = ['pre/post rmspe']
        for panel in panels:
            if panel not in valid_panels:
                raise ValueError(
                    '"{}" is not a valid panel. Valid panels are: {}.'.format(
                        panel, ', '.join(['"{}"'.format(e) for e in valid_panels])
                    )
                )
            if panel in solo_panels and len(panels) > 1:
                print("{} is meant to have a different x-axis, plotting it together with other plots may hide that").format(panel)
                #warning.warn('Validity plots should be plotted alone', PlotWarning)
                
        
        n_panels = len(panels)
        ax = plt.subplot(n_panels, 1, 1)
        idx = 1

        if 'original' in panels:
            ax.set_title("{} vs. {}".format(treated_label, synth_label))
            ax.plot(time, synth.T, 'r--', label=synth_label)
            ax.plot(time ,self.treated_outcome_all, 'b-', label=treated_label)
            ax.axvline(self.treatment_period-1, linestyle=':', color="gray")
            ax.annotate(treatment_label, 
                xy=(self.treatment_period-1, self.treated_outcome[-1]*1.2),
                xytext=(-160, -4),
                xycoords='data',
                #textcoords="data",
                textcoords='offset points',
                arrowprops=dict(arrowstyle="->"))
            ax.set_ylabel(self.outcome_var)
            ax.set_xlabel(self.time)
            ax.legend()
            if idx != n_panels:
                plt.setp(ax.get_xticklabels(), visible=False)
            idx += 1

        if 'pointwise' in panels:

            ax = plt.subplot(n_panels, 1, idx, sharex=ax)
            #Subtract outcome of synth from both synth and treated outcome
            normalized_treated_outcome = self.treated_outcome_all - synth.T
            normalized_synth = np.zeros(self.periods_all)
            most_extreme_value = np.max(np.absolute(normalized_treated_outcome))

            ax.set_title("Pointwise Effects")
            ax.plot(time, normalized_synth, 'r--', label=synth_label)
            ax.plot(time ,normalized_treated_outcome, 'b-', label=treated_label)
            ax.axvline(self.treatment_period-1, linestyle=':', color="gray")
            ax.set_ylim(-1.1*most_extreme_value, 1.1*most_extreme_value)
            ax.annotate(treatment_label, 
                xy=(self.treatment_period-1, 0.5*most_extreme_value),
                xycoords='data',
                xytext=(-160, -4),
                textcoords='offset points',
                arrowprops=dict(arrowstyle="->"))
            ax.set_ylabel(self.outcome_var)
            ax.set_xlabel(self.time)
            ax.legend()
            if idx != n_panels:
                plt.setp(ax.get_xticklabels(), visible=False)
            idx += 1

        if 'cumulative' in panels:
            ax = plt.subplot(n_panels, 1, idx, sharex=ax)
            #Compute cumulative treatment effect as cumulative sum of pointwise effects
            cumulative_effect = np.cumsum(normalized_treated_outcome[self.periods_pre_treatment:])
            cummulative_treated_outcome = np.concatenate((np.zeros(self.periods_pre_treatment), cumulative_effect), axis=None)
            normalized_synth = np.zeros(self.periods_all)

            ax.set_title("Cumulative Effects")
            ax.plot(time, normalized_synth, 'r--', label=synth_label)
            ax.plot(time ,cummulative_treated_outcome, 'b-', label=treated_label)
            ax.axvline(self.treatment_period-1, linestyle=':', color="gray")
            #ax.set_ylim(-1.1*most_extreme_value, 1.1*most_extreme_value)
            ax.annotate(treatment_label, 
                xy=(self.treatment_period-1, cummulative_treated_outcome[-1]*0.3),
                xycoords='data',
                xytext=(-160, -4),
                textcoords='offset points',
                arrowprops=dict(arrowstyle="->"))
            ax.set_ylabel(self.outcome_var)
            ax.set_xlabel(self.time)
            ax.legend()
            if idx != n_panels:
                plt.setp(ax.get_xticklabels(), visible=False)
            idx += 1

        if 'in-space placebo' in panels:
            #assert self.in_space_placebos != None, "Must run in_space_placebo() before you can plot!"
            
            ax = plt.subplot(n_panels, 1, idx)
            zero_line = np.zeros(self.periods_all)
            normalized_treated_outcome = self.treated_outcome_all - synth.T
            
            ax.set_title("In-space placebo's")
            ax.plot(time, zero_line, 'k--')

            #Plot each placebo
            ax.plot(time, self.in_space_placebos[0], ('0.7'), label="Placebos")
            for i in range(1, self.n_controls):

                #If the pre rmspe is not more than
                #in_space_exclusion_multiple times larger than synth pre rmspe
                if in_space_exclusion_multiple is not None:
                  if self.pre_post_rmspe_ratio["pre_rmspe"][i] < in_space_exclusion_multiple*self.pre_post_rmspe_ratio["pre_rmspe"][0]:
                      ax.plot(time, self.in_space_placebos[i], ('0.7'))
                else:
                  ax.plot(time, self.in_space_placebos[i], ('0.7'))

            ax.axvline(self.treatment_period-1, linestyle=':', color="gray")
            ax.plot(time, normalized_treated_outcome, 'b-', label=treated_label)

            #ax.set_ylim(-1.1*most_extreme_value, 1.1*most_extreme_value)
            '''
            ax.annotate(treatment_label,
                xy=(self.treatment_period-1, self.treated_outcome[-1]*1.2),
                xycoords='data',
                xytext=(-160, -4),
                textcoords='offset points',
                arrowprops=dict(arrowstyle="->"))
            '''
            ax.set_ylabel(self.outcome_var)
            ax.set_xlabel(self.time)
            ax.legend()
            if idx != n_panels:
                plt.setp(ax.get_xticklabels(), visible=False)
            idx += 1

        if 'pre/post rmspe' in panels:
            #assert self.pre_post_rmspe_ratio != None, "Must run in_space_placebo() before you can plot!"
            
            ax = plt.subplot(n_panels, 1, idx)
            
            ax.set_title("Pre/post treatment root mean square prediction error")
    
            ax.hist(self.pre_post_rmspe_ratio["post/pre"], bins=int(max(self.pre_post_rmspe_ratio["post/pre"])), 
                    color="#3F5D7D", histtype='bar', ec='black')
            
            ax.annotate(self.treated_unit,
                xy=(self.pre_post_rmspe_ratio["post/pre"][0]-0.5, 1),
                xycoords='data',
                xytext=(-100, 80),
                textcoords='offset points',
                arrowprops=dict(arrowstyle="->"))
            
            ax.set_ylabel("Frequency")
            ax.set_xlabel("Ratio")
            if idx != n_panels:
                plt.setp(ax.get_xticklabels(), visible=False)
            idx += 1

        if 'in-time placebo' in panels:

            ax = plt.subplot(n_panels, 1, idx)
            ax.set_title("In-time placebo: {} vs. {}".format(treated_label, synth_label))

            ax.plot(time, self.in_time_placebo_outcome.T, 'r--', label=synth_label)
            ax.plot(time ,self.treated_outcome_all, 'b-', label=treated_label)

            ax.axvline(self.placebo_treatment_period, linestyle=':', color="gray")
            ax.annotate('Placebo Treatment', 
                xy=(self.placebo_treatment_period, self.treated_outcome_all[self.placebo_periods_pre_treatment]*1.2),
                xytext=(-160, -4),
                xycoords='data',
                textcoords='offset points',

                arrowprops=dict(arrowstyle="->"))
            ax.set_ylabel(self.outcome_var)
            ax.set_xlabel(self.time)
            ax.legend()

            if idx != n_panels:
                plt.setp(ax.get_xticklabels(), visible=False)
            idx += 1

        fig.tight_layout(pad=3.0)
        plt.show()

    def _get_plotter(self):  # pragma: no cover
        """Some environments do not have matplotlib. Importing the library through
        this method prevents import exceptions.

        Returns:
          plotter: `matplotlib.pyplot
        """
        import matplotlib.pyplot as plt
        return plt