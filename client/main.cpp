#include <QApplication>
#include <QMainWindow>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLineEdit>
#include <QTextEdit>
#include <QPushButton>
#include <QListWidget>
#include <QLabel>
#include <QFileDialog>
#include <QSettings>
#include <QNetworkAccessManager>
#include <QNetworkRequest>
#include <QNetworkReply>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QMessageBox>
#include <QUrlQuery>

#ifdef Q_OS_ANDROID
#include <QtAndroid>
#include <QAndroidJniObject>
#endif

class NotesApp : public QMainWindow {
    Q_OBJECT
public:
    NotesApp(QWidget *parent = nullptr) : QMainWindow(parent) {
        setupUi();
        loadSettings();
        connectSignals();
    }

private:
    QLineEdit *serverUrlEdit;
    QLineEdit *usernameEdit;
    QLineEdit *passwordEdit;
    QLineEdit *titleEdit;
    QTextEdit *contentEdit;
    QPushButton *loginButton;
    QPushButton *saveSettingsButton;
    QPushButton *createNoteButton;
    QPushButton *selectFileButton;
    QListWidget *notesList;
    QWidget *loginWidget;
    QWidget *mainWidget;
    QWidget *settingsWidget;
    QNetworkAccessManager *networkManager;
    QString token;
    QString serverUrl;
    QString selectedFilePath;

    void setupUi() {
        networkManager = new QNetworkAccessManager(this);

        // Login screen
        loginWidget = new QWidget(this);
        QVBoxLayout *loginLayout = new QVBoxLayout(loginWidget);
        usernameEdit = new QLineEdit(loginWidget);
        usernameEdit->setPlaceholderText("Username");
        passwordEdit = new QLineEdit(loginWidget);
        passwordEdit->setPlaceholderText("Password");
        passwordEdit->setEchoMode(QLineEdit::Password);
        loginButton = new QPushButton("Login", loginWidget);
        QPushButton *settingsButton = new QPushButton("Settings", loginWidget);
        loginLayout->addWidget(new QLabel("Login", loginWidget));
        loginLayout->addWidget(usernameEdit);
        loginLayout->addWidget(passwordEdit);
        loginLayout->addWidget(loginButton);
        loginLayout->addWidget(settingsButton);

        // Settings screen
        settingsWidget = new QWidget(this);
        QVBoxLayout *settingsLayout = new QVBoxLayout(settingsWidget);
        serverUrlEdit = new QLineEdit(settingsWidget);
        serverUrlEdit->setPlaceholderText("Server URL (e.g., https://your-domain.com)");
        saveSettingsButton = new QPushButton("Save", settingsWidget);
        QPushButton *cancelSettingsButton = new QPushButton("Cancel", settingsWidget);
        settingsLayout->addWidget(new QLabel("Settings", settingsWidget));
        settingsLayout->addWidget(serverUrlEdit);
        settingsLayout->addWidget(saveSettingsButton);
        settingsLayout->addWidget(cancelSettingsButton);

        // Main screen
        mainWidget = new QWidget(this);
        QVBoxLayout *mainLayout = new QVBoxLayout(mainWidget);
        titleEdit = new QLineEdit(mainWidget);
        titleEdit->setPlaceholderText("Note Title");
        contentEdit = new QTextEdit(mainWidget);
        selectFileButton = new QPushButton("Select File", mainWidget);
        createNoteButton = new QPushButton("Create Note", mainWidget);
        notesList = new QListWidget(mainWidget);
        QPushButton *mainSettingsButton = new QPushButton("Settings", mainWidget);
        mainLayout->addWidget(mainSettingsButton);
        mainLayout->addWidget(titleEdit);
        mainLayout->addWidget(contentEdit);
        mainLayout->addWidget(selectFileButton);
        mainLayout->addWidget(createNoteButton);
        mainLayout->addWidget(notesList);

        // Initial screen
        setCentralWidget(settingsWidget); // Show settings if server URL is not set
    }

    void loadSettings() {
        QSettings settings("NotesApp", "NotesApp");
        serverUrl = settings.value("serverUrl", "").toString();
        token = settings.value("token", "").toString();
        serverUrlEdit->setText(serverUrl);
        if (!serverUrl.isEmpty()) {
            setCentralWidget(loginWidget);
            if (!token.isEmpty()) {
                setCentralWidget(mainWidget);
                fetchNotes();
            }
        }
    }

    void connectSignals() {
        connect(loginButton, &QPushButton::clicked, this, &NotesApp::onLogin);
        connect(saveSettingsButton, &QPushButton::clicked, this, &NotesApp::onSaveSettings);
        connect(createNoteButton, &QPushButton::clicked, this, &NotesApp::onCreateNote);
        connect(selectFileButton, &QPushButton::clicked, this, &NotesApp::onSelectFile);
        connect(findChild<QPushButton*>("Settings"), &QPushButton::clicked, this, &NotesApp::onShowSettings);
        connect(findChild<QPushButton*>("Cancel"), &QPushButton::clicked, this, &NotesApp::onCancelSettings);
        connect(notesList, &QListWidget::itemClicked, this, &NotesApp::onNoteSelected);
    }

private slots:
    void onLogin() {
        QUrlQuery postData;
        postData.addQueryItem("username", usernameEdit->text());
        postData.addQueryItem("password", passwordEdit->text());
        QNetworkRequest request(QUrl(serverUrl + "/token"));
        request.setHeader(QNetworkRequest::ContentTypeHeader, "application/x-www-form-urlencoded");
        QNetworkReply *reply = networkManager->post(request, postData.toString(QUrl::FullyEncoded).toUtf8());
        connect(reply, &QNetworkReply::finished, this, [=]() {
            if (reply->error() == QNetworkReply::NoError) {
                QJsonDocument doc = QJsonDocument::fromJson(reply->readAll());
                token = doc.object().value("access_token").toString();
                QSettings settings("NotesApp", "NotesApp");
                settings.setValue("token", token);
                setCentralWidget(mainWidget);
                fetchNotes();
            } else {
                QMessageBox::warning(this, "Error", "Login failed");
            }
            reply->deleteLater();
        });
    }

    void onSaveSettings() {
        serverUrl = serverUrlEdit->text();
        QSettings settings("NotesApp", "NotesApp");
        settings.setValue("serverUrl", serverUrl);
        setCentralWidget(loginWidget);
    }

    void onShowSettings() {
        serverUrlEdit->setText(serverUrl);
        setCentralWidget(settingsWidget);
    }

    void onCancelSettings() {
        if (serverUrl.isEmpty()) {
            QMessageBox::warning(this, "Error", "Server URL must be set");
        } else {
            setCentralWidget(token.isEmpty() ? loginWidget : mainWidget);
        }
    }

    void onSelectFile() {
#ifdef Q_OS_ANDROID
        // Android file picker
        QAndroidJniObject intent = QAndroidJniObject::fromString("android.intent.action.OPEN_DOCUMENT");
        QAndroidJniObject intentObj("android/content/Intent", "()V");
        intentObj.callObjectMethod("setAction", "(Ljava/lang/String;)Landroid/content/Intent;", intent.object());
        intentObj.callObjectMethod("addCategory", "(Ljava/lang/String;)Landroid/content/Intent;", QAndroidJniObject::fromString("android.intent.category.OPENABLE").object());
        intentObj.callObjectMethod("setType", "(Ljava/lang/String;)Landroid/content/Intent;", QAndroidJniObject::fromString("*/*").object());
        QtAndroid::startActivity(intentObj, 100, [=](int requestCode, int resultCode, const QAndroidJniObject &data) {
            if (requestCode == 100 && resultCode == -1) {
                QAndroidJniObject uri = data.callObjectMethod("getData", "()Landroid/net/Uri;");
                selectedFilePath = uri.callObjectMethod("toString", "()Ljava/lang/String;").toString();
                selectFileButton->setText("File: " + selectedFilePath.split('/').last());
            }
        });
#else
        // Desktop file picker
        selectedFilePath = QFileDialog::getOpenFileName(this, "Select File");
        if (!selectedFilePath.isEmpty()) {
            selectFileButton->setText("File: " + selectedFilePath.split('/').last());
        }
#endif
    }

    void onCreateNote() {
        QHttpMultiPart *multiPart = new QHttpMultiPart(QHttpMultiPart::FormDataType);
        QHttpPart titlePart;
        titlePart.setHeader(QNetworkRequest::ContentDispositionHeader, QVariant("form-data; name=\"title\""));
        titlePart.setBody(titleEdit->text().toUtf8());
        QHttpPart contentPart;
        contentPart.setHeader(QNetworkRequest::ContentDispositionHeader, QVariant("form-data; name=\"content\""));
        contentPart.setBody(contentEdit->toPlainText().toUtf8());
        multiPart->append(titlePart);
        multiPart->append(contentPart);

        if (!selectedFilePath.isEmpty()) {
            QFile *file = new QFile(selectedFilePath);
            if (file->open(QIODevice::ReadOnly)) {
                QHttpPart filePart;
                filePart.setHeader(QNetworkRequest::ContentDispositionHeader, QVariant("form-data; name=\"file\"; filename=\"" + selectedFilePath.split('/').last() + "\""));
                filePart.setBodyDevice(file);
                file->setParent(multiPart);
                multiPart->append(filePart);
            }
        }

        QNetworkRequest request(QUrl(serverUrl + "/notes/"));
        request.setHeader(QNetworkRequest::ContentTypeHeader, "multipart/form-data; boundary=" + multiPart->boundary());
        request.setRawHeader("Authorization", "Bearer " + token.toUtf8());
        QNetworkReply *reply = networkManager->post(request, multiPart);
        multiPart->setParent(reply);
        connect(reply, &QNetworkReply::finished, this, [=]() {
            if (reply->error() == QNetworkReply::NoError) {
                titleEdit->clear();
                contentEdit->clear();
                selectedFilePath.clear();
                selectFileButton->setText("Select File");
                fetchNotes();
            } else {
                QMessageBox::warning(this, "Error", "Failed to create note");
            }
            reply->deleteLater();
        });
    }

    void onNoteSelected(QListWidgetItem *item) {
        QString noteId = item->data(Qt::UserRole).toString();
        QNetworkRequest request(QUrl(serverUrl + "/notes/" + noteId));
        request.setRawHeader("Authorization", "Bearer " + token.toUtf8());
        QNetworkReply *reply = networkManager->get(request);
        connect(reply, &QNetworkReply::finished, this, [=]() {
            if (reply->error() == QNetworkReply::NoError) {
                QJsonDocument doc = QJsonDocument::fromJson(reply->readAll());
                QJsonObject note = doc.object();
                QMessageBox::information(this, note.value("title").toString(), note.value("content").toString());
            }
            reply->deleteLater();
        });
    }

    void fetchNotes() {
        QNetworkRequest request(QUrl(serverUrl + "/notes/"));
        request.setRawHeader("Authorization", "Bearer " + token.toUtf8());
        QNetworkReply *reply = networkManager->get(request);
        connect(reply, &QNetworkReply::finished, this, [=]() {
            if (reply->error() == QNetworkReply::NoError) {
                notesList->clear();
                QJsonDocument doc = QJsonDocument::fromJson(reply->readAll());
                QJsonArray notes = doc.array();
                for (const QJsonValue &value : notes) {
                    QJsonObject note = value.toObject();
                    QString title = note.value("title").toString();
                    QListWidgetItem *item = new QListWidgetItem(title, notesList);
                    item->setData(Qt::UserRole, note.value("id").toString());
                }
            }
            reply->deleteLater();
        });
    }
};

#include "main.moc"

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);
    NotesApp window;
    window.show();
    return app.exec();
}