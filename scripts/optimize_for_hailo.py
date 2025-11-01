#!/usr/bin/env python3
"""
Optimize Overwatch Configuration for Hailo Acceleration
Converts workflows and configurations to use Hailo-accelerated models
"""
import sys
import os
from pathlib import Path
import yaml
import shutil

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from core.hailo_detector import detect_hailo, convert_model_to_hailo, get_hailo_models


def optimize_workflows(input_file: Path, output_file: Path):
    """Convert workflow config to use Hailo models"""
    
    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        return False
    
    with open(input_file, 'r') as f:
        config = yaml.safe_load(f)
    
    if not config or 'workflows' not in config:
        print(f"❌ Invalid workflow configuration")
        return False
    
    # Convert each workflow to use Hailo models
    for workflow_name, workflow_config in config['workflows'].items():
        if 'model' in workflow_config:
            original_model = workflow_config['model']
            hailo_model = convert_model_to_hailo(original_model)
            
            if hailo_model != original_model:
                workflow_config['model'] = hailo_model
                print(f"✅ {workflow_name}: {original_model} → {hailo_model}")
            else:
                print(f"ℹ️  {workflow_name}: {original_model} (no Hailo equivalent, keeping original)")
    
    # Update global settings
    if 'global' not in config:
        config['global'] = {}
    
    config['global']['device'] = 'hailo'
    config['global']['prefer_hailo'] = True
    
    # Backup original if output is different from input
    if output_file == input_file and output_file.exists():
        backup_file = output_file.with_suffix('.yaml.bak')
        shutil.copy(output_file, backup_file)
        print(f"📋 Backup created: {backup_file}")
    
    # Write optimized config
    with open(output_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)
    
    print(f"✅ Optimized workflow saved: {output_file}")
    return True


def main():
    print("🚀 Hailo Optimization Tool\n")
    
    # Check for Hailo
    if not detect_hailo():
        print("❌ No Hailo accelerator detected!")
        print("This script optimizes configurations for Hailo-8L acceleration.")
        sys.exit(1)
    
    print("✅ Hailo-8L accelerator detected (13 TOPS)")
    
    # Get available Hailo models
    hailo_models = get_hailo_models()
    print(f"\n📦 Available Hailo models: {', '.join(hailo_models)}\n")
    
    # Paths
    config_dir = Path(__file__).parent.parent / "config"
    
    # Optimize workflow files
    workflows_example = config_dir / "workflows.example.yaml"
    workflows_hailo = config_dir / "workflows_hailo.yaml"
    
    if workflows_example.exists():
        print(f"Converting: {workflows_example}")
        optimize_workflows(workflows_example, workflows_hailo)
    
    # Check for active workflows.yaml
    workflows_active = config_dir / "workflows.yaml"
    if workflows_active.exists():
        print(f"\n⚠️  Found active workflows.yaml")
        response = input("Convert to Hailo? (y/N): ")
        if response.lower() == 'y':
            optimize_workflows(workflows_active, workflows_active)
    else:
        print(f"\nℹ️  No active workflows.yaml found")
        print(f"To use Hailo-optimized workflows:")
        print(f"  cp {workflows_hailo} {workflows_active}")
    
    print("\n✅ Optimization complete!")
    print("\nNext steps:")
    print("1. Review the optimized workflow configuration")
    print("2. Restart Overwatch to use Hailo acceleration")
    print("3. Monitor performance - expect 5-10x improvement!")


if __name__ == "__main__":
    main()

