from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QLineEdit,
    QVBoxLayout,
)


def main():
    app = QApplication([])

    window = QWidget()
    window.setWindowTitle("GUI Test")

    label = QLabel("Hello Qt!")
    entry = QLineEdit()
    entry.setPlaceholderText("Enter new label text")

    button = QPushButton("Update Label")

    def update_label():
        text = entry.text() or "Button clicked!"
        label.setText(text)

    button.clicked.connect(update_label)

    layout = QVBoxLayout()
    layout.addWidget(label)
    layout.addWidget(entry)
    layout.addWidget(button)
    window.setLayout(layout)

    window.show()
    app.exec_()


if __name__ == "__main__":
    main()
