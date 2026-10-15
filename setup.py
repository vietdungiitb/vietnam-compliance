from setuptools import find_packages, setup

with open("requirements.txt") as f:
    install_requires = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="vietnam_compliance",
    version="0.2.0",
    description="Vietnam Statutory Compliance & Localization for Frappe / ERPNext v16 (TT 200/133, NQ 202/2025/QH15 34 Tỉnh thành, Thuế GTGT/TNCN, Hóa đơn điện tử T-VAN 02GTTT/01GTKT)",
    author="Edusuccess & Open Source Contributors",
    author_email="tech@edusuccess.vn",
    url="https://github.com/vietdungiitb/vietnam-compliance",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
    license="GPL-3.0",
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
)
