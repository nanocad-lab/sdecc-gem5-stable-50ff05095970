$GEM5_DIR/build/X86/gem5.fast\
 \
 --outdir=$OUTPUT_DIR\
 \
 $GEM5_DIR/configs/example/my_se.py\
 \
 --cpu-type=timing\
 --num-cpus=1\
 --sys-clock="2GHz"\
 --cpu-clock="2GHz"\
 --sys-voltage="1V"\
 \
 --mem-type=ddr3_1600_x64\
 --mem-channels=1\
 --mem-size="2048MB"\
 \
 --benchmark=$BENCHMARK\
 --program_stdout=$OUTPUT_DIR/$BENCHMARK.out\
 --program_stderr=$OUTPUT_DIR/$BENCHMARK.err\
 \
 --maxinsts=100000000\
 --fast-forward=10000000\
 --at-instruction