import React, { useState } from 'react'
import { Card, Form, Input, Button, message, Switch, Row, Col } from 'antd'
import { SaveOutlined, SettingOutlined } from '@ant-design/icons'

const SystemSettings: React.FC = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  const onFinish = async () => {
    setLoading(true)
    try {
      // 这里可以添加保存设置的API调用
      message.success('系统设置保存成功')
    } catch (error) {
      message.error('保存失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0 }}>
          <SettingOutlined style={{ marginRight: 8 }} />
          系统设置
        </h2>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="基本设置" size="small">
            <Form
              form={form}
              layout="vertical"
              onFinish={onFinish}
              initialValues={{
                site_name: '化学文献解析系统',
                site_description: '专业的化学文献智能解析平台',
                max_upload_size: 50,
                enable_registration: true,
              }}
            >
              <Form.Item
                label="站点名称"
                name="site_name"
                rules={[{ required: true, message: '请输入站点名称' }]}
              >
                <Input placeholder="请输入站点名称" />
              </Form.Item>

              <Form.Item
                label="站点描述"
                name="site_description"
              >
                <Input.TextArea placeholder="请输入站点描述" rows={3} />
              </Form.Item>

              <Form.Item
                label="最大上传文件大小 (MB)"
                name="max_upload_size"
                rules={[{ required: true, message: '请输入最大上传文件大小' }]}
              >
                <Input type="number" placeholder="请输入最大上传文件大小" />
              </Form.Item>

              <Form.Item
                label="启用用户注册"
                name="enable_registration"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading} icon={<SaveOutlined />}>
                  保存设置
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="安全设置" size="small">
            <Form
              layout="vertical"
              initialValues={{
                require_email_verification: true,
                enable_captcha: false,
                session_timeout: 60,
              }}
            >
              <Form.Item
                label="需要邮箱验证"
                name="require_email_verification"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                label="启用验证码"
                name="enable_captcha"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                label="会话超时时间 (分钟)"
                name="session_timeout"
                rules={[{ required: true, message: '请输入会话超时时间' }]}
              >
                <Input type="number" placeholder="请输入会话超时时间" />
              </Form.Item>

              <Form.Item>
                <Button type="primary" icon={<SaveOutlined />}>
                  保存设置
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default SystemSettings