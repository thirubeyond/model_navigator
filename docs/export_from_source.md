<!--
Copyright (c) 2021-2022, NVIDIA CORPORATION. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

# Export from Source

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Requirements](#requirements)
- [Installation](#installation)
- [Exporting from source](#exporting-from-source)
  - [Model export](#model-export)
- [Model verification](#model-verification)
  - [Model conversion test](#model-conversion-test)
  - [Correctness test](#correctness-test)
  - [Performance evaluation](#performance-evaluation)
  - [Manual verification](#manual-verification)
- [Results](#results)
  - [Navigator workspace](#navigator-workspace)
  - [Package descriptor](#package-descriptor)
  - [Saved samples](#saved-samples)
  - [Saving and loading .nav package](#saving-and-loading-nav-package)
- [Examples](#examples)
  - [PyTorch export](#pytorch-export)
  - [Example TensorFlow](#example-tensorflow)
- [API](#api)
  - [Export PyTorch](#export-pytorch)
  - [Export TensorFlow 2](#export-tensorflow-2)
  - [Package Descriptor](#package-descriptor)
  - [Package Save](#package-save)
  - [Package Load](#package-load)
  - [Package Profile](#package-profile)
- [Reproducibility](#reproducibility)
  - [Export](#export)
  - [Conversion](#conversion)
- [Contrib](#contrib)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


## Requirements
To use Model Navigator Export API you have to have PyTorch or TensorFlow2 already installed on your system.
To export models to TensorRT you have to have [NVIDIA TensorRT](https://developer.nvidia.com/tensorrt) installed.

NGC Containers are the recommended environments for Model Navigator, they have all required dependencies:
- [PyTorch](https://catalog.ngc.nvidia.com/orgs/nvidia/containers/pytorch)
- [TensorFlow](https://catalog.ngc.nvidia.com/orgs/nvidia/containers/tensorflow)

## Installation

To install Model Navigator use command:

```shell
$ pip install --extra-index-url https://pypi.ngc.nvidia.com git+https://github.com/triton-inference-server/model_navigator.git@v0.3.3#egg=model-navigator[<extras,>] --upgrade
```

Extras:
* pyt - Model Navigator for PyTorch
* tf - Model Navigator for TensorFlow2
* cli - Model Navigator CLI
* huggingface - Model Navigator with HuggingFace


## Exporting from source
Model Navigator export process is based on commands that are executed in order.
Steps described below represent core functionality related to export and model verification.

### Model export
Exports model from framework source code to binary format.

Supported output formats for TensorFlow2:
- SavedModel

Supported output formats for PyTorch:
- ONNX
- Torch-TensorRT
- TorchScript

## Model verification

### Model conversion test
Convert model from exported format to target format.
We perform the set of conversion to test functionality. Main purpose of this step is to test conversion paths for model.
For optimal performance you have to do conversion on production target with Model Navigator CLI.

Supported conversions for TensorFlow2:
- SavedModel to TensorFlow-TensorRT SavedModel
- SavedModel to ONNX
- ONNX to TensorRT

Supported conversions for PyTorch:
- ONNX to TensorRT

### Correctness test
Step uses outputs from exported model and source model for output correctness comparison with absolute tolerance and
relative tolerance provided by the user. Additionally, it calculates true absolute and relative tolerance for all model outputs,
for each format and runtime.


- Absolute tolerance is calculated as element-wise maximal difference between values in source and exported model outputs.
- Relative tolerance is calculated as element-wise maximal difference between values in source and exported model outputs,
divided by absolute value of exported model output.

### Performance evaluation
After conversions Model Navigator performs a set of performance tests in different configurations to
verify if given format has proper performance optimizations and provides speedup.

### Manual verification
Additionally to correctness and performance verification user may write custom
code that measures other metrics on exported models.
Model Navigator export function returns a PackageDescriptor object that helps with accessing generated models.
With this, user can perform additional tests (e.g. accuracy verification)
on loaded model and set model state to verified.


## Results

### Navigator workspace
Workspace is not intended for distribution. Use `.nav` package generated by ```PackageDecriptor.save(<path>)```.

Export results are stored inside ```navigator_workdir``` directory in ```<model_name>.nav.workspace``` directory.

```model_input``` directory contains input samples generated by dataloader saved to Numpy npz format.

```model_output``` directory contains output data returned from model saved to Numpy npz format.

```navigator.log``` contains logs generated by Model Navigator API and error message from run.

```status.yaml``` contains status of exported models, Model Navigator API configuration and information about environment.

Each format related directory contains exported model and ```config.yaml``` that can be used as input for Model Navigator CLI.

```
navigator_workdir
└── navigator_model.nav.workspace
    ├── status.yaml
    ├── navigator.log
    ├── model_input
    │   ├── conversion
    │   │   └── 0.npz
    │   ├── correctness
    │   │   ├── 0.npz
    │   │   ├── 1.npz
    │   │   ├── 2.npz
    │   ├── profiling
    │   │   └── 0.npz
    ├── model_output
    │   ├── conversion
    │   │   └── 0.npz
    │   ├── correctness
    │   │   ├── 0.npz
    │   │   ├── 1.npz
    │   │   ├── 2.npz
    │   ├── profiling
    │   │   └── 0.npz
    ├── onnx
    │   ├── config.yaml
    │   └── model.onnx
    ├── trt-fp16
    │   ├── config.yaml
    │   └── model.pt
    ├── trt-fp32
    │   ├── config.yaml
    │   └── model.pt
    ├── torch-trt-script
    │   ├── config.yaml
    │   └── model.pt
    ├── torch-trt-trace
    │   ├── config.yaml
    │   └── model.pt
    ├── torchscript-script
    │   ├── config.yaml
    │   └── model.pt
    └── torchscript-trace
        ├── config.yaml
        └── model.pt
```

### Package descriptor
If after export you still want to work on your model, Model Navigator API gives you nice interface to check the status
and interact with different parts of exported and converted formats.
Additionally, model verification tests (e.g. accuracy, business metrics) cannot be done automatically. User should
verify converted models after exporting them, by setting the verified state for particular formats after executing custom
test scenarios.
After veryfing the models user have to save the package to the ```.nav``` package format.


### Saved samples

Model Navigator saves samples and corresponding outputs to perform conversions, profiling and verify correctness later on in the deployment process. Samples are separated into following directories:

* ```conversion/``` - samples that span the dimension variability in the dataloader (e.g. the longest and the shortest sequence, the smallest and the largest picture),
* ```correctness/``` - ```sample_count``` (defaults to 100) random samples,
* ```performance/``` - one random sample.

Model Navigator does not save the full batches but rather extracts single samples from the dataloader. Batches are reconstruced from the samples by repeating the samples along the batch dimension.

### Saving and loading .nav package
After export the results must be saved into a ```.nav``` package with ```PackageDecriptor.save(<path>)``` method. This ```.nav``` package can be then shared for further testing or optimization for Triton Inference Server.

Saved ```.nav``` package can be loaded back into the Model Navigator API with ```nav.load(<path>)``` function.

## Examples

### PyTorch export
```python
import torch
import model_navigator as nav

device = "cuda" if torch.cuda.is_available() else "cpu"

dataloader = [torch.full((3, 5), 1.0, device=device) for _ in range(10)]

model = torch.nn.Linear(5, 7).to(device).eval()

package_desc = nav.torch.export(
    model=model,
    model_name="example_model",
    dataloader=dataloader,
    opset=13,
    input_names=("input",),
    dynamic_axes={"input": {0: "batch"}},
)

onnx_status = package_desc.get_status(format=nav.Format.ONNX)
if onnx_status:
    onnx_runner = package_desc.get_runner(format=nav.Format.ONNX, runtime=nav.RuntimeProvider.CPU)

# Additional model verification ...
model_is_valid = True # code for model verification
if model_is_valid:
    package_desc.set_verified(format=nav.Format.ONNX, runtime=nav.RuntimeProvider.CPU)

package_desc.save("example_pyt.nav")

loaded_package_desc = nav.load("example_pyt.nav")
```

### Example TensorFlow
```python
import tensorflow as tf
import model_navigator as nav

dataloader = [tf.random.uniform(shape=[1, 224, 224, 3], minval=0, maxval=1, dtype=tf.dtypes.float32) for _ in range(10)]

inp = tf.keras.layers.Input((1, 224, 224, 3))
layer_output = tf.keras.layers.Lambda(lambda x: x)(inp)
layer_output = tf.keras.layers.Lambda(lambda x: x)(layer_output)
model_output = tf.keras.layers.Lambda(lambda x: x)(layer_output)
model = tf.keras.Model(inp, model_output)

package_desc = nav.tensorflow.export(
    model=model,
    model_name="example_tf2_model",
    dataloader=dataloader,
    override_workdir=True,
    input_names=("input",),
)

onnx_status = package_desc.get_status(format=nav.Format.ONNX)
if onnx_status:
    onnx_runner = package_desc.get_runner(format=nav.Format.ONNX, runtime=nav.RuntimeProvider.CPU)

# Additional model verification ...
model_is_valid = True # code for model verification
if model_is_valid:
    package_desc.set_verified(format=nav.Format.ONNX, runtime=nav.RuntimeProvider.CPU)

package_desc.save("example_tf2.nav")

loaded_package_desc = nav.load("example_tf2.nav")
```

## API
### Export PyTorch

```python
def export(
    model: torch.nn.Module,
    dataloader: SizedDataLoader, # has to implement len() and iter()
    model_name: Optional[str] = None,
    opset: Optional[int] = None, # ONNX opset, by default latest is used
    target_formats: Optional[Union[Union[str, Format], Tuple[Union[str, Format], ...]]] = None,
    jit_options: Optional[Union[Union[str, JitType], Tuple[Union[str, JitType], ...]]] = None,
    workdir: Optional[Path] = None, # default workdir is navigator_workdir in current working directory
    override_workdir: bool = False,
    sample_count: Optional[int] = None, # number of samples that will be saved from dataloader
    atol: Optional[float] = None, # absolute tolerance used for correctness tests. If None, value will be calculated during run
    rtol: Optional[float] = None, # relative tolerance used for correctness tests. If None, value will be calculated during run
    input_names: Optional[Tuple[str, ...]] = None, # model input name in the same order as in samples returned from dataloader
    output_names: Optional[Tuple[str, ...]] = None,
    dynamic_axes: Optional[Dict[str, Union[Dict[int, str], List[int]]]] = None, # for ONNX export, see https://pytorch.org/docs/1.9.1/onnx.html#functions
    trt_dynamic_axes: Optional[Dict[str, Dict[int, Tuple[int, int, int]]]] = None,
    target_precisions: Optional[Union[Union[str, TensorRTPrecision], Tuple[Union[str, TensorRTPrecision], ...]]] = None,
    precison_mode: Optional[Union[str, TensorRTPrecisionMode]] = None,  # use single or hierarchy precision for TorchTRT conversion
    max_workspace_size: Optional[int] = None,
    target_device: Optional[str] = None, # target device for exporting the model
    disable_git_info: bool = False,
    batch_dim: Optional[int] = 0,
    onnx_runtimes: Optional[Union[Union[str, RuntimeProvider], Tuple[Union[str, RuntimeProvider], ...]]] = None, # defaults to all available runtimes
    run_profiling: bool = True,
    profiler_config: Optional[ProfilerConfig] = None,
) -> PackageDescriptor:
    """Function exports PyTorch model to all supported formats."""
```

### Export TensorFlow 2
```python
def export(
    model,
    dataloader: SizedDataLoader, # has to implement len() and iter()
    target_precisions: Optional[Union[Union[str, TensorRTPrecision], Tuple[Union[str, TensorRTPrecision], ...]]] = None,
    max_workspace_size: Optional[int] = None,
    minimum_segment_size: int = 3,
    model_name: Optional[str] = None,
    target_formats: Optional[Union[Union[str, Format], Tuple[Union[str, Format], ...]]] = None,
    workdir: Optional[Path] = None, # default workdir is navigator_workdir in current working directory
    override_workdir: bool = False,
    sample_count: Optional[int] = None, # number of samples that will be saved from dataloader
    opset: Optional[int] = None,
    atol: Optional[float] = None, # absolute tolerance used for correctness tests. If None, value will be calculated during run
    rtol: Optional[float] = None, # relative tolerance used for correctness tests. If None, value will be calculated during run
    input_names: Optional[Tuple[str, ...]] = None, # model input name in the same order as in samples returned from dataloader
    output_names: Optional[Tuple[str, ...]] = None,
    dynamic_axes: Optional[Dict[str, Union[Dict[int, str], List[int]]]] = None,
    trt_dynamic_axes: Optional[Dict[str, Dict[int, Tuple[int, int, int]]]] = None,
    disable_git_info: bool = False,
    batch_dim: Optional[int] = 0,
    onnx_runtimes: Optional[Union[Union[str, RuntimeProvider], Tuple[Union[str, RuntimeProvider], ...]]] = None, # defaults to all available runtimes
    run_profiling: bool = True,
    profiler_config: Optional[ProfilerConfig] = None,
) -> PackageDescriptor:
    """Exports TensorFlow 2 model to all supported formats."""
```

### Package Descriptor
```python
def get_formats_status(self) -> Dict:
    """Return dictionary of pairs Format : Bool. True for successful exports, False for failed exports."""
```

```python
def get_formats_performance(self) -> Dict:
    """Return dictionary of pairs Format : Float with information about the median latency [ms] for each format."""
```

```python
def get_status(
    self,
    format: Format,
    runtime_provider: Optional[RuntimeProvider] = None,
    jit_type: Optional[JitType] = None,
    precision: Optional[TensorRTPrecision] = None,
) -> bool:
    """Return status (True or False) of export operation for particular format, jit_type,
    precision and runtime_provider."""
```


```python
def get_model(
    self,
    format: Format,
    jit_type: Optional[JitType] = None,
    precision: Optional[TensorRTPrecision] = None
):
    """
    Load exported model for given format, jit_type and precision and return model object

    :return
        model object for TensorFlow, PyTorch and ONNX
        model path for TensorRT
    """
```
```python
def get_runner(
    self,
    format: Format,
    jit_type: Optional[JitType] = None,
    precision: Optional[TensorRTPrecision] = None,
    runtime: Optional[RuntimeProvider] = None,
):
    """
    Load exported model for given format, jit_type and precision and return Polygraphy runner for given runtime.

    :return
        Polygraphy BaseRunner object: https://github.com/NVIDIA/TensorRT/blob/main/tools/Polygraphy/polygraphy/backend/base/runner.py
    """
```
```python
def set_verified(
    self,
    format: Format,
    runtime: RuntimeProvider,
    jit_type: Optional[JitType] = None,
    precision: Optional[TensorRTPrecision] = None,
):
    """Set exported model verified for given format, jit_type and precision"""
```

### Package Save

```.nav``` packages are created with ```nav.save()``` function.

```python
def save(
    package_descriptor: PackageDescriptor,
    path: Union[str, Path],
    keep_workdir: bool = True,
    override: bool = False,
    save_data: bool = True,
) -> None:
    """Save export results into the .nav package at given path.
        If `keep_workdir = False` remove the working directory.
        If `override = True` override `path`.
        If `save_data = False` discard samples from the dataloader.
        That won't allow for correctness check later on in the deployment process.
    """
```

### Package Load

```.nav``` packages can be load back to the Model Navigator with ```nav.load()``` function.

```python
def load(
    path: Union[str, Path],
    workdir: Optional[Union[str, Path]] = None,
    override_workdir: bool = False,
    retest_conversions: bool = True,
    run_profiling: Optional[bool] = None,
    profiler_config: Optional[ProfilerConfig] = None,
    target_device: Optional[str] = None,
) -> PackageDescriptor:
    """Load .nav package from the path.
        If `retest_conversions = True` rerun conversion tests.
    """
```

### Package Profile

```python
def profile(package_descriptor: PackageDescriptor, profiler_config: Optional[ProfilerConfig] = None) -> None:
    """
    Run profiling on the package for each batch size from the `profiler_config.batch_sizes`.
    """
```

Profiling is configured by `ProfilerConfig`. Profiler is based on [Triton Performance Analyzer](https://github.com/triton-inference-server/server/blob/main/docs/perf_analyzer.md), please refer to [Triton Performance Analyzer](https://github.com/triton-inference-server/server/blob/main/docs/perf_analyzer.md) documentation for more info.

```python
class ProfilerConfig(DataObject):
    batch_sizes: Optional[Sequence[int]] = None # list of batch sizes to profile, defaults to (1, <dataloader_batch_size>)
    measurement_mode: MeasurementMode = MeasurementMode.COUNT_WINDOWS # MeasurementMode.TIME_WINDOWS - Fixed duriation of a window, MeasurementMode.COUNT_WINDOWS - fixed number of requests in a window
    measurement_interval: Optional[float] = 5000  # ms, length of measurment windows (MeasurementMode.TIME_WINDOWS)
    measurement_request_count: Optional[int] = 50 # number of requests in a window (MeasurementMode.COUNT_WINDOWS)
    stability_percentage: float = 10.0 # How much average latency can vary between windows to accept the results as stable
    max_trials: int = 10 # Maximum number of measurement windows to get 3 stable windows
```

## Reproducibility

When a given export or conversion fails Model Navigator prepares script to reproduce and debug the error. In the log it will show a specific command that runs the script. For example:

```bash
model_navigator.framework_api.exceptions.UserError: Command to reproduce error:
/opt/conda/bin/python3 /workspace/navigator_workdir/resnet50_pyt.nav.workspace/onnx/reproduce.py --exported_model_path /workspace navigator_workdir/resnet50_pyt.nav.workspace/onnx/model.onnx --opset 14 --input_names ["image"] --output_names ["logits"] --dynamic_axes {"image": [0]} --package_path /workspace/navigator_workdir/resnet50_pyt.nav.workspace --batch_dim 0 --forward_kw_names None --target_device cuda
```

This command can be run by the user from the command line and the script is as minimalistic as possible to allow for easy investigation.

Some conversions directly use other tools (e.g. [Polygraphy](https://docs.nvidia.com/deeplearning/tensorrt/polygraphy/docs/index.html)). In this case the command to reproduce the error will also directly call the external tool without any overhead. Example:

```bash
model_navigator.framework_api.exceptions.UserError: Command to reproduce error:
polygraphy convert /workspace/navigator_workdir/resnext101-32x4d_pyt.nav.workspace/onnx/model.onnx --convert-to trt -o /workspace/navigator_workdir/resnext101-32x4d_pyt.nav.workspace/trt-fp32/model.plan --trt-min-shapes mage:[1,3,224
,224] --trt-opt-shapes image:[10,3,224,224] --trt-max-shapes image:[10,3,224,224] --workspace=8589934592
```


### Export

Export needs the model object as an input and user must provide the `get_model()` function in the script to reproduce the error.

Here is an example of reproducing script for ONNX export:
```python
from typing import Dict, List, Optional

import fire
import torch

from model_navigator.framework_api.utils import load_samples


def get_model():
    raise NotImplementedError("Please implement the get_model() function to reproduce the export error.")


def export(
    exported_model_path: str,
    opset: int,
    input_names: List[str],
    output_names: List[str],
    dynamic_axes: Dict[str, Dict[int, str]],
    package_path: str,
    batch_dim: Optional[int],
    forward_kw_names: Optional[List[str]],
    target_device: str,
):
    model = get_model()
    profiling_sample = load_samples("profiling_sample", package_path, batch_dim)

    dummy_input = tuple(torch.from_numpy(val).to(target_device) for val in profiling_sample.values())
    if forward_kw_names is not None:
        dummy_input = ({key: val for key, val in zip(forward_kw_names, dummy_input)},)

    torch.onnx.export(
        model,
        args=dummy_input,
        f=exported_model_path,
        verbose=False,
        opset_version=opset,
        input_names=input_names,
        output_names=output_names,
        dynamic_axes=dynamic_axes,
    )


if __name__ == "__main__":
    fire.Fire(export)
```

### Conversion

Conversion scirpts are fully stand-alone as they operate on checkpoints. They can be run without any modifications.

Example for SavedModel to TF-TRT conversion:

```python
import fire
from tensorflow.python.compiler.tensorrt import trt_convert as trtc

from model_navigator.framework_api.utils import load_samples, sample_to_tuple


def convert(
    exported_model_path: str,
    converted_model_path: str,
    max_workspace_size: int,
    target_precision: str,
    minimum_segment_size: int,
    package_path: str,
    batch_dim: int,
):

    conversion_samples = load_samples("conversion_samples", package_path, batch_dim)

    def _dataloader():
        for sample in conversion_samples:
            yield sample_to_tuple(sample)

    params = trtc.DEFAULT_TRT_CONVERSION_PARAMS._replace(
        max_workspace_size_bytes=max_workspace_size,
        precision_mode=target_precision,
        minimum_segment_size=minimum_segment_size,
    )
    converter = trtc.TrtGraphConverterV2(
        input_saved_model_dir=exported_model_path, use_dynamic_shape=True, conversion_params=params
    )

    converter.convert()
    converter.build(_dataloader)
    converter.save(converted_model_path)


if __name__ == "__main__":
    fire.Fire(convert)

```

## Contrib

In the `model_navigator.contrib` module you can find helper functions for specific model providers.

Contrib modules:

* [HuggingFace](../model_navigator/framework_api/contrib/huggingface/)
