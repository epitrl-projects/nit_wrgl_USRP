#!/usr/bin/python3
#
# Copyright 2010,2012,2013 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
#

from gnuradio import gr
from gnuradio import blocks
from gnuradio import filter
import sys
import numpy

try:
    from gnuradio import analog
except ImportError:
    sys.stderr.write("Error: Program requires gr-analog.\n")
    sys.exit(1)

try:
    from matplotlib import pyplot
except ImportError:
    sys.stderr.write(
        "Error: Program requires matplotlib (see: matplotlib.sourceforge.net).\n")
    sys.exit(1)


def main():
    N = 1000000
    fs = 8000

    freqs = [100, 200, 300, 400, 500]
    nchans = 7

    sigs = list()
    fmtx = list()
    for fi in freqs:
        s = analog.sig_source_f(fs, analog.GR_SIN_WAVE, fi, 1)
        fm = analog.nbfm_tx(fs, 4 * fs, max_dev=10000,
                            tau=75e-6, fh=0.925 * (4 * fs) / 2.0)
        sigs.append(s)
        fmtx.append(fm)

    syntaps = filter.firdes.low_pass_2(
        len(freqs), fs, fs / float(nchans) / 2, 100, 100)
    print("Synthesis Num. Taps = %d (taps per filter = %d)" % (len(syntaps),
                                                               len(syntaps) / nchans))
    chtaps = filter.firdes.low_pass_2(
        len(freqs), fs, fs / float(nchans) / 2, 100, 100)
    print("Channelizer Num. Taps = %d (taps per filter = %d)" % (len(chtaps),
                                                                 len(chtaps) / nchans))
    filtbank = filter.pfb_synthesizer_ccf(nchans, syntaps)
    channelizer = filter.pfb.channelizer_ccf(nchans, chtaps)

    noise_level = 0.01
    head = blocks.head(gr.sizeof_gr_complex, N)
    noise = analog.noise_source_c(analog.GR_GAUSSIAN, noise_level)
    addnoise = blocks.add_cc()
    snk_synth = blocks.vector_sink_c()

    tb = gr.top_block()

    tb.connect(noise, (addnoise, 0))
    tb.connect(filtbank, head, (addnoise, 1))
    tb.connect(addnoise, channelizer)
    tb.connect(addnoise, snk_synth)

    snk = list()
    for i, si in enumerate(sigs):
        tb.connect(si, fmtx[i], (filtbank, i))

    for i in range(nchans):
        snk.append(blocks.vector_sink_c())
        tb.connect((channelizer, i), snk[i])

    tb.run()

    if 1:
        channel = 1
        data = snk[channel].data()[1000:]

        f1 = pyplot.figure(1)
        s1 = f1.add_subplot(1, 1, 1)
        s1.plot(data[10000:10200])
        s1.set_title(("Output Signal from Channel %d" % channel))

        fftlen = 2048
        winfunc = numpy.blackman
        #winfunc = numpy.hamming

        f2 = pyplot.figure(2)
        s2 = f2.add_subplot(1, 1, 1)
        s2.psd(data, NFFT=fftlen,
               Fs=nchans * fs,
               noverlap=fftlen / 4,
               window=lambda d: d * winfunc(fftlen))
        s2.set_title(("Output PSD from Channel %d" % channel))

        f3 = pyplot.figure(3)
        s3 = f3.add_subplot(1, 1, 1)
        s3.psd(snk_synth.data()[1000:], NFFT=fftlen,
               Fs=nchans * fs,
               noverlap=fftlen / 4,
               window=lambda d: d * winfunc(fftlen))
        s3.set_title("Output of Synthesis Filter")

        pyplot.show()


if __name__ == "__main__":
    main()
