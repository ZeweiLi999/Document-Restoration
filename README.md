# 文档复原软件

## ![Static Badge](https://img.shields.io/badge/Language-语言-8A2BE2) 选择你的语言：

- [简体中文](readme/readme_CN.md)
- [English](readme/readme_EN.md)

## ![Static Badge](https://img.shields.io/badge/Function-功能-blue) 功能：
**实现：PyQT6 + PyTorch**

**核心功能：**
- [x] 去阴影
- [x] 文字提取
- [x] 去模糊
- [x] 外观增强
- [ ] 压缩复原
- [ ] 折叠复原

**前端优化：**
- [ ] 进度显示
- [ ] 多重优化

### 去阴影功能：
<img src="https://github.com/user-attachments/assets/7ddefb98-afd3-42e2-a59f-ca2f84e6ca72" alt="89de2cc669a072c36de638d22f03576" width=600 height=450/>


<br />

### 提取文字功能：
<img src="https://github.com/user-attachments/assets/4072b245-37ae-4364-ae21-33eab45c5763" alt="89de2cc669a072c36de638d22f03576" width=600 height=450/>

<br />

### 去模糊功能
<img src="https://github.com/user-attachments/assets/741961f1-780d-4b50-b5e8-088a368909c9" alt="89de2cc669a072c36de638d22f03576" width=600 height=450/>

<br />

### 外观增强功能：
<img src="https://github.com/user-attachments/assets/643beca7-9e5f-4b28-bddb-fc588cd94267" alt="89de2cc669a072c36de638d22f03576" width=600 height=450/>




## ![Static Badge](https://img.shields.io/badge/Installation-安装-red) 安装：

### 0. 安装环境：

   
   **CPU版本**
   
   ```
   conda create -n dr python=3.9
   conda activate dr
   pip install -r requirements_cpu.txt
   ```
   
   **GPU版本**

   ```
   conda create -n dr python=3.9
   conda activate dr
   pip install -r requirements_gpu.txt
   ```

   
### 2. 下载模型权重：
   将模型权重 [docres.pkl](https://1drv.ms/f/s!Ak15mSdV3Wy4iahoKckhDPVP5e2Czw?e=iClwdK) 放至 `./pth/`
<br />
<br />
### 3. 运行run_demo.py

   ```
   python run_demo.py
   ```
