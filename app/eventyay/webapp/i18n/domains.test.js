/**
 * Tests for Django gettext source templates and Webapps unified JSON translations.
 */
import test from 'node:test'
import assert from 'node:assert/strict'
import {existsSync, readFileSync} from 'node:fs'
import {fileURLToPath} from 'node:url'
import path from 'node:path'
import {importFromApp} from './app-deps.js'
import {mergeCatalogWithEnglish} from './catalog.js'
import {createI18nRuntime} from './runtime.js'

const {default: i18next} = await importFromApp('i18next')

const i18nDir = path.dirname(fileURLToPath(import.meta.url))
const localeRoot = path.resolve(i18nDir, '../../locale')
const localesRoot = path.resolve(i18nDir, '../locales')

function readJsonCatalog(lang) {
	return JSON.parse(readFileSync(path.join(localesRoot, `${lang}.json`), 'utf8'))
}

test('gettext source language for Django is pot templates, not English po files', () => {
	for (const domain of ['django', 'djangojs']) {
		assert.ok(existsSync(path.join(localeRoot, `${domain}.pot`)), `${domain}.pot is missing`)
		assert.equal(
			existsSync(path.join(localeRoot, 'en', 'LC_MESSAGES', `${domain}.po`)),
			false,
			`${domain} must not ship locale/en/LC_MESSAGES/${domain}.po next to ${domain}.pot`
		)
	}
})

test('webapp unified en.json exists and contains frontend keys', () => {
	assert.ok(existsSync(path.join(localesRoot, 'en.json')), 'locales/en.json is missing')
	const en = readJsonCatalog('en')
	assert.ok(Object.hasOwn(en, 'Schedule'))
	assert.ok(Object.hasOwn(en, 'Search'))
	assert.ok(Object.hasOwn(en, 'Save'))
	assert.ok(Object.hasOwn(en, 'Admin mode'))
})

test('webapp JSON runtime translates German and falls back to English for missing keys', async () => {
	const en = readJsonCatalog('en')
	const de = {
		Schedule: 'Zeitplan',
		Save: 'Speichern',
	}

	const runtime = createI18nRuntime({
		i18next: i18next.createInstance(),
		localeLoaders: {
			'/locales/en.json': async () => ({default: en}),
			'/locales/de.json': async () => ({default: de}),
		},
		warnOnMissing: false,
	})

	await runtime.init({lng: 'de'})
	assert.equal(runtime.translate('Schedule'), 'Zeitplan')
	assert.equal(runtime.translate('Save'), 'Speichern')
	// Missing in German falls back to English
	assert.equal(runtime.translate('Search'), 'Search')

	await runtime.changeLanguage('hi')
	// Untranslated language falls back to English
	assert.equal(runtime.translate('Schedule'), 'Schedule')
})
