/* A form for uploading Scrapy projects */

var React = require("react");
var { Panel, Button, FormGroup, FormControl, ControlLabel, Alert } = require("react-bootstrap");


export var ProjectUpload = React.createClass({
    getInitialState: function () {
        return {
            projectName: "",
            selectedFile: null,
            uploading: false,
            message: null,
            messageType: null,
            isExpanded: false
        };
    },

    render: function () {
        var formStyle = {
            marginTop: '10px'
        };

        return (
            <Panel 
                collapsible 
                expanded={this.state.isExpanded}
                onSelect={this.handleToggle}
                header="Upload Scrapy Project" 
                bsStyle="info">
                {this.state.message && (
                    <Alert bsStyle={this.state.messageType}>
                        {this.state.message}
                    </Alert>
                )}
                <form onSubmit={this.handleSubmit} style={formStyle}>
                    <FormGroup>
                        <ControlLabel>Project Name</ControlLabel>
                        <FormControl
                            type="text"
                            value={this.state.projectName}
                            onChange={this.handleProjectNameChange}
                            placeholder="Enter project name (e.g., myproject)"
                            disabled={this.state.uploading}
                        />
                    </FormGroup>
                    
                    <FormGroup>
                        <ControlLabel>Project Archive</ControlLabel>
                        <FormControl
                            type="file"
                            accept=".zip,.tar,.tar.gz,.tgz"
                            onChange={this.handleFileChange}
                            disabled={this.state.uploading}
                        />
                        <span className="help-block">
                            Upload a zip or tar.gz file containing your Scrapy project
                        </span>
                    </FormGroup>
                    
                    <Button 
                        type="submit" 
                        bsStyle="primary"
                        disabled={this.state.uploading || !this.state.projectName || !this.state.selectedFile}>
                        {this.state.uploading ? 'Uploading...' : 'Upload Project'}
                    </Button>
                </form>
            </Panel>
        );
    },

    handleToggle: function() {
        this.setState({isExpanded: !this.state.isExpanded});
    },

    handleProjectNameChange: function (e) {
        this.setState({projectName: e.target.value});
    },

    handleFileChange: function (e) {
        var file = e.target.files[0];
        this.setState({selectedFile: file});
    },

    handleSubmit: function (e) {
        e.preventDefault();
        
        if (!this.state.projectName || !this.state.selectedFile) {
            return;
        }

        this.setState({
            uploading: true,
            message: null,
            messageType: null
        });

        var formData = new FormData();
        formData.append('project_name', this.state.projectName);
        formData.append('project_file', this.state.selectedFile);

        fetch('/project/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.message || 'Upload failed');
                });
            }
            return response.json();
        })
        .then(data => {
            this.setState({
                uploading: false,
                message: 'Project uploaded successfully! Spider packages: ' + (data.spider_packages || []).join(', '),
                messageType: 'success',
                projectName: '',
                selectedFile: null
            });
            // Reset file input
            var fileInput = document.querySelector('input[type="file"]');
            if (fileInput) {
                fileInput.value = '';
            }
        })
        .catch(error => {
            this.setState({
                uploading: false,
                message: 'Upload failed: ' + error.message,
                messageType: 'danger'
            });
        });
    }
});
