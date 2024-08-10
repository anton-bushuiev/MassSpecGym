# Reproduced from https://github.com/pluskal-lab/DreaMS/blob/main/dreams/models/layers/fourier_features.py

import torch
import torch.nn as nn
from math import ceil


class FourierFeatures(nn.Module):
    """
    A module for generating Fourier features for input data. This module maps input data
    to a higher-dimensional space using sinusoidal functions, enhancing the representation
    capabilities for various tasks.

    Args:
        strategy (str): Strategy for generating frequency components. Available options are
            'random', 'voronov_et_al', and 'dreams'. Each option corresponds to a certain paper:
            - 'random': https://doi.org/10.48550/arXiv.2006.10739.
            - 'voronov_et_al': https://doi.org/10.48550/arXiv.2207.02980.
            - 'dreams': https://doi.org/10.26434/chemrxiv-2023-kss3r-v2.
        x_min (float, optional): The minimum value for generating frequencies. Defaults to 1e-4.
        x_max (float, optional): The maximum value for generating frequencies. Defaults to 1000.
        trainable (bool, optional): If True, the frequencies are treated as trainable parameters.
            Defaults to False.
        funcs (str, optional): Specifies the trigonometric functions to use. Options are 'both',
            'sin', and 'cos'. Defaults to 'both'.
        sigma (float, optional): Standard deviation used for random frequency initialization
            when strategy is 'random'. Defaults to 10.
        num_freqs (int, optional): Number of frequency components to generate. Defaults to 512.
    """

    def __init__(
        self,
        strategy,
        x_min=1e-4,
        x_max=1000,
        trainable=False,
        funcs="both",
        sigma=10,
        num_freqs=512,
    ):
        assert funcs in {"both", "sin", "cos"}, "funcs must be 'both', 'sin', or 'cos'"
        assert 0 < x_min < 1, "x_min must be a positive fraction"

        super().__init__()
        self.funcs = funcs
        self.strategy = strategy
        self.trainable = trainable
        self.num_freqs = num_freqs

        if strategy == "random":
            self.b = torch.randn(num_freqs) * sigma
        elif self.strategy == "voronov_et_al":
            self.b = torch.tensor(
                [
                    1 / (x_min * (x_max / x_min) ** (2 * i / (num_freqs - 2)))
                    for i in range(1, num_freqs)
                ],
            )
        elif self.strategy == "dreams":
            self.b = torch.tensor(
                [1 / (x_min * i) for i in range(2, ceil(1 / x_min), 2)]
                + [1 / (1 * i) for i in range(2, ceil(x_max), 1)],
            )
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        self.b = self.b.unsqueeze(0)
        self.b = nn.Parameter(self.b, requires_grad=self.trainable)
        self.register_parameter("Fourier frequencies", self.b)

    @property
    def num_features(self):
        """
        Returns the number of features generated by the FourierFeatures module.
        If both sine and cosine functions are used, the number of features is doubled.

        Returns:
            int: The number of features.
        """
        return self.b.shape[1] if self.funcs != "both" else 2 * self.b.shape[1]

    def forward(self, x):
        """
        Applies the Fourier transformation to the input data.

        Args:
            x (torch.Tensor): Input tensor of shape (batch_size, input_dim) to transform.

        Returns:
            torch.Tensor: Fourier features.
        """
        x = 2 * torch.pi * x @ self.b

        if self.funcs == "both":
            x = torch.cat((torch.cos(x), torch.sin(x)), dim=-1)
        elif self.funcs == "cos":
            x = torch.cos(x)
        elif self.funcs == "sin":
            x = torch.sin(x)

        return x
