#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  8 22:48:08 2023

@author: rob
"""

import scipy.io
import matplotlib.pyplot as plt
import numpy as np
import pandas
from scipy.optimize import curve_fit


mat = scipy.io.loadmat('psfData.mat')



def sigmoid(x, a, b, c, d):
    y = a + (b - a) / (1 + np.exp(-c * (x - d)));
    return y 

def FWHM(x,y):
    ind = np.argmax(y)
    halfCurve = y[0:ind]
    halfMax = y[ind]/2
    ind = np.argmin(abs(halfCurve-halfMax))
    return np.round(abs(x[ind])*2)


x = mat['psfData']['x'][0][0].flatten()
y = mat['psfData']['y'][0][0].flatten()

guess = [0.4,0, 1,0] # Initial guess for the parameters

popt, pcov = curve_fit(sigmoid, x, y, p0=guess)


# These are the raw data that we fit
if False:
    plt.plot(x, y, 'o', label='data')
    plt.plot(x, sigmoid(x, *popt), label='fit')
    plt.legend()
    plt.show()


# Generate the PSF
x_psf = np.linspace(x.min(), x.max(),1000);

PDF = np.diff(sigmoid(x_psf, *popt)) / np.diff(x_psf);
PDF = PDF*-1; # TODO: hard-coded and assumes we go from high to low

x_psf = x_psf[1::]

# Centre the curve at zero
ind = np.argmax(PDF)
x_psf = x_psf - x_psf[ind]
x_psf = x_psf * 1E3; # convert to microns



# Get the FWHM
FWHM_measured = FWHM(x_psf,PDF)

#Scale the PDF
PDF = PDF/PDF.max()

# Read in the fit from Zemax

z = pandas.read_csv('zemax_psf_150mm_08.txt')
FWHM_theory = FWHM(z['position'],z['value'])


# Plot the PSF from the fit to the sigmoid
fig = plt.figure('PSF')
fig.clf()
ax = fig.add_subplot(1,1,1)

ax.plot(z['position'],z['value'],'-k')
ax.plot(x_psf,PDF,'-r')
ax.grid(True)

ax.set_title('FWHM: theory = %d microns, measured = %d microns' % (FWHM_theory,FWHM_measured))
ax.set_xlim((-500,500))
ax.legend(('Theory (Zemax)', 'Measured'))

plt.savefig('psf.png')
