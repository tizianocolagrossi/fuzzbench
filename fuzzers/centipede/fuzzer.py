# Copyright 2022 Google LLC
#
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
"""Integration code for centipede fuzzer."""

import subprocess
import os

from fuzzers import utils


def build():
    """Build benchmark."""
    # TODO(Dongge): Check if they support trace-dataflow.
    # TODO(Dongge): Build targets with sanitizers.
    cflags = ['-fsanitize-coverage=trace-pc-guard,pc-table,trace-cmp']
    utils.append_flags('CFLAGS', cflags)
    utils.append_flags('CXXFLAGS', cflags)

    os.environ['CC'] = 'clang'
    os.environ['CXX'] = 'clang++'
    os.environ['FUZZER_LIB'] = (
        '/src/centipede/bazel-bin/libfuzz_target_runner.a '
        '/src/centipede/bazel-bin/libfuzz_target_runner_no_main.a '
        '/src/centipede/bazel-bin/libshared_memory_blob_sequence.a '
        '/src/centipede/bazel-bin/libexecution_request.a '
        '/src/centipede/bazel-bin/libexecution_result.a '
        '/src/centipede/bazel-bin/libbyte_array_mutator.a')

    utils.build_benchmark()


def fuzz(input_corpus, output_corpus, target_binary):
    """Run fuzzer. Wrapper that uses the defaults when calling
    run_fuzzer."""
    run_fuzzer(input_corpus, output_corpus, target_binary)


def run_fuzzer(input_corpus, output_corpus, target_binary, extra_flags=None):
    """Run fuzzer."""
    if extra_flags is None:
        extra_flags = []

    # Seperate out corpus and crash directories as sub-directories of
    # |output_corpus| to avoid conflicts when corpus directory is reloaded.
    crashes_dir = os.path.join(output_corpus, 'crashes')
    output_corpus = os.path.join(output_corpus, 'corpus')
    work_dir = os.path.join(output_corpus, 'WD')
    os.makedirs(crashes_dir)
    os.makedirs(output_corpus)
    os.makedirs(work_dir)

    flags = [
        f'--workdir={work_dir}',
        f'--corpus_dir={output_corpus},{input_corpus}'
        f'--binary={target_binary}',
        '--num_runs=100',
        # Run in fork mode to allow ignoring ooms, timeouts, crashes and
        # continue fuzzing indefinitely.
        '--fork_server=1',
        '--timeout=0',
    ]
    dictionary_path = utils.get_dictionary_path(target_binary)
    if dictionary_path:
        flags.append(f'--dictionary={dictionary_path}')

    command = ['/out/centipede'] + flags
    print('[run_fuzzer] Running command: ' + ' '.join(command))
    subprocess.check_call(command)
