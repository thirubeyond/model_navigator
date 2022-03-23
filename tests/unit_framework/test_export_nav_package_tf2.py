# Copyright (c) 2021-2022, NVIDIA CORPORATION. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# pytype: disable=import-error
import tempfile
from pathlib import Path

import tensorflow

import model_navigator as nav

# pytype: enable=import-error


def check_model_dir(model_dir: Path, format: nav.Format) -> bool:
    if not model_dir.is_dir():
        return False
    if not Path(model_dir / "config.yaml").is_file():
        return False
    if format == nav.Format.ONNX:
        model_path = model_dir / "model.onnx"
    elif format == nav.Format.TENSORRT:
        model_path = model_dir / "model.plan"
    else:
        model_path = model_dir / "model.savedmodel"
    if not Path(model_path).exists():
        return False
    return True


dataloader = [
    tensorflow.random.uniform(shape=[1, 224, 224, 3], minval=0, maxval=1, dtype=tensorflow.dtypes.float32)
    for _ in range(10)
]

inp = tensorflow.keras.layers.Input((224, 224, 3))
layer_output = tensorflow.keras.layers.Lambda(lambda x: x)(inp)
layer_output = tensorflow.keras.layers.Lambda(lambda x: x)(layer_output)
layer_output = tensorflow.keras.layers.Lambda(lambda x: x)(layer_output)
layer_output = tensorflow.keras.layers.Lambda(lambda x: x)(layer_output)
layer_output = tensorflow.keras.layers.Lambda(lambda x: x)(layer_output)
model_output = tensorflow.keras.layers.Lambda(lambda x: x)(layer_output)

model = tensorflow.keras.Model(inp, model_output)


def test_tf2_export_savedmodel():
    with tempfile.TemporaryDirectory() as tmp_dir:
        model_name = "navigator_model"

        workdir = Path(tmp_dir) / "navigator_workdir"
        package_dir = workdir / f"{model_name}.nav"
        status_file = package_dir / "status.yaml"
        model_input_dir = package_dir / "model_input"
        model_output_dir = package_dir / "model_output"
        navigator_log_file = package_dir / "navigator.log"

        nav.tensorflow.export(
            model=model,
            dataloader=dataloader,
            workdir=workdir,
            model_name=model_name,
            override_workdir=True,
            target_formats=(nav.Format.TF_SAVEDMODEL,),
        )

        assert status_file.is_file()
        assert model_input_dir.is_dir()
        assert all(
            [path.suffix == ".npz" for samples_dir in model_input_dir.iterdir() for path in samples_dir.iterdir()]
        )
        assert model_output_dir.is_dir()
        assert all(
            [path.suffix == ".npz" for samples_dir in model_output_dir.iterdir() for path in samples_dir.iterdir()]
        )
        assert navigator_log_file.is_file()

        # Output formats
        assert check_model_dir(model_dir=package_dir / "tf-savedmodel", format=nav.Format.TF_SAVEDMODEL)

        # Formats not exported
        assert check_model_dir(model_dir=package_dir / "tf-trt-fp16", format=nav.Format.TF_SAVEDMODEL) is False
        assert check_model_dir(model_dir=package_dir / "tf-trt-fp32", format=nav.Format.TF_SAVEDMODEL) is False


def test_tf2_export_tf_trt():
    with tempfile.TemporaryDirectory() as tmp_dir:
        model_name = "navigator_model"

        workdir = Path(tmp_dir) / "navigator_workdir"
        package_dir = workdir / f"{model_name}.nav"
        status_file = package_dir / "status.yaml"
        model_input_dir = package_dir / "model_input"
        model_output_dir = package_dir / "model_output"
        navigator_log_file = package_dir / "navigator.log"

        nav.tensorflow.export(
            model=model,
            dataloader=dataloader,
            workdir=workdir,
            model_name=model_name,
            override_workdir=True,
            target_formats=(nav.Format.TF_TRT,),
        )

        assert status_file.is_file()
        assert model_input_dir.is_dir()
        assert all(
            [path.suffix == ".npz" for samples_dir in model_input_dir.iterdir() for path in samples_dir.iterdir()]
        )
        assert model_output_dir.is_dir()
        assert all(
            [path.suffix == ".npz" for samples_dir in model_output_dir.iterdir() for path in samples_dir.iterdir()]
        )
        assert navigator_log_file.is_file()

        # Output formats
        assert check_model_dir(model_dir=package_dir / "tf-trt-fp16", format=nav.Format.TF_SAVEDMODEL)
        assert check_model_dir(model_dir=package_dir / "tf-trt-fp32", format=nav.Format.TF_SAVEDMODEL)

        # Formats not exported but present as step for tf-trt
        assert check_model_dir(model_dir=package_dir / "tf-savedmodel", format=nav.Format.TF_SAVEDMODEL)


def test_tf2_export_tf_onnx():
    with tempfile.TemporaryDirectory() as tmp_dir:
        model_name = "navigator_model"

        workdir = Path(tmp_dir) / "navigator_workdir"
        package_dir = workdir / f"{model_name}.nav"
        status_file = package_dir / "status.yaml"
        model_input_dir = package_dir / "model_input"
        model_output_dir = package_dir / "model_output"
        navigator_log_file = package_dir / "navigator.log"

        nav.tensorflow.export(
            model=model,
            dataloader=dataloader,
            workdir=workdir,
            model_name=model_name,
            override_workdir=True,
            target_formats=(nav.Format.ONNX,),
        )

        assert status_file.is_file()
        assert model_input_dir.is_dir()
        assert all(
            [path.suffix == ".npz" for samples_dir in model_input_dir.iterdir() for path in samples_dir.iterdir()]
        )
        assert model_output_dir.is_dir()
        assert all(
            [path.suffix == ".npz" for samples_dir in model_output_dir.iterdir() for path in samples_dir.iterdir()]
        )
        assert navigator_log_file.is_file()

        # Output formats
        assert check_model_dir(model_dir=package_dir / "onnx", format=nav.Format.ONNX)

        # Formats not exported but present as step for onnx
        assert check_model_dir(model_dir=package_dir / "tf-savedmodel", format=nav.Format.TF_SAVEDMODEL)

# TODO Fix onnx to trt conversion or test for TensorFlow2
# def test_tf2_export_trt():
#     with tempfile.TemporaryDirectory() as tmp_dir:
#         model_name = "navigator_model"
#
#         workdir = Path(tmp_dir) / "navigator_workdir"
#         package_dir = workdir / f"{model_name}.nav"
#         status_file = package_dir / "status.yaml"
#         model_input_dir = package_dir / "model_input"
#         model_output_dir = package_dir / "model_output"
#         navigator_log_file = package_dir / "navigator.log"
#
#         nav.tensorflow.export(
#             model=model,
#             dataloader=dataloader,
#             workdir=workdir,
#             model_name=model_name,
#             override_workdir=True,
#             target_formats=(nav.Format.TENSORRT,),
#         )
#
#         assert status_file.is_file()
#         assert model_input_dir.is_dir()
#         assert all(
#             [path.suffix == ".npz" for samples_dir in model_input_dir.iterdir() for path in samples_dir.iterdir()]
#         )
#         assert model_output_dir.is_dir()
#         assert all(
#             [path.suffix == ".npz" for samples_dir in model_output_dir.iterdir() for path in samples_dir.iterdir()]
#         )
#         assert navigator_log_file.is_file()
#
#         # Output formats
#         assert check_model_dir(model_dir=package_dir / "trt-fp16", format=nav.Format.TENSORRT)
#         assert check_model_dir(model_dir=package_dir / "trt-fp32", format=nav.Format.TENSORRT)
#
#         # Formats not exported but present as step for TRT
#         assert check_model_dir(model_dir=package_dir / "tf-savedmodel", format=nav.Format.TF_SAVEDMODEL)


def test_tf2_export_string_format():
    with tempfile.TemporaryDirectory() as tmp_dir:
        model_name = "navigator_model"

        workdir = Path(tmp_dir) / "navigator_workdir"
        package_dir = workdir / f"{model_name}.nav"
        status_file = package_dir / "status.yaml"
        model_input_dir = package_dir / "model_input"
        model_output_dir = package_dir / "model_output"
        navigator_log_file = package_dir / "navigator.log"

        nav.tensorflow.export(
            model=model,
            dataloader=dataloader,
            workdir=workdir,
            model_name=model_name,
            override_workdir=True,
            target_formats="tf-trt",
            target_precisions="fp32",
        )

        assert status_file.is_file()
        assert model_input_dir.is_dir()
        assert all(
            [path.suffix == ".npz" for samples_dir in model_input_dir.iterdir() for path in samples_dir.iterdir()]
        )
        assert model_output_dir.is_dir()
        assert all(
            [path.suffix == ".npz" for samples_dir in model_output_dir.iterdir() for path in samples_dir.iterdir()]
        )
        assert navigator_log_file.is_file()

        # Output formats
        assert check_model_dir(model_dir=package_dir / "tf-trt-fp16", format=nav.Format.TF_SAVEDMODEL) is False
        assert check_model_dir(model_dir=package_dir / "tf-trt-fp32", format=nav.Format.TF_SAVEDMODEL)

        # Formats not exported but present as step for tf-trt
        assert check_model_dir(model_dir=package_dir / "tf-savedmodel", format=nav.Format.TF_SAVEDMODEL)
