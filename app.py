#!/usr/bin/env python3
"""
Computer Graphics Assignment 1.1: Basic Shapes
Course: CO3059 - Computer Graphics
HCMUT
"""

import glfw
from viewer import Viewer


def main():
    if not glfw.init():
        return
    
    try:
        viewer = Viewer()
        viewer.run()
    finally:
        glfw.terminate()


if __name__ == '__main__':
    main()
