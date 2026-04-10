"""Configuration loader for PitchIQ."""
from pathlib import Path
from typing import Any, Dict, List
import yaml


class Config:
    """Central configuration manager."""
    
    def __init__(self, config_dir: Path = None):
        if config_dir is None:
            config_dir = Path(__file__).parent.parent / "configs"
        self.config_dir = config_dir
        self._cache: Dict[str, Any] = {}
    
    def load(self, config_name: str) -> Dict[str, Any]:
        """Load a configuration file."""
        if config_name in self._cache:
            return self._cache[config_name]
        
        config_path = self.config_dir / f"{config_name}.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        self._cache[config_name] = config
        return config
    
    def get_seasons(self) -> Dict[str, Any]:
        """Get season configuration."""
        features_config = self.load('features')
        return features_config.get('seasons', {
            'current': '2425',
            'previous': '2324',
            'training_seasons': ['2324', '2223', '2122']
        })
    
    def get_rolling_window_size(self, window_type: str = 'short') -> int:
        """Get rolling window size."""
        features_config = self.load('features')
        return features_config['rolling_windows'][window_type]
    
    def get_model_params(self, model_name: str) -> Dict[str, Any]:
        """Get model hyperparameters."""
        model_config = self.load('model')
        return model_config['models'].get(model_name, {})


# Global config instance
config = Config()


def get_current_season() -> str:
    """Get current season code."""
    return config.get_seasons()['current']


def get_previous_season() -> str:
    """Get previous season code."""
    return config.get_seasons()['previous']


def get_training_seasons() -> List[str]:
    """Get list of seasons to use for training."""
    return config.get_seasons().get('training_seasons', ['2324', '2223'])
